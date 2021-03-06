#!/bin/bash -i

###Converted from AttractEasyModel by easy2model 1.3
### Generated by ATTRACT shell script generator version 0.8

set -u -e
if [ ! -f $ATTRACTDIR/attract ]; then
  echo 'Cannot find the ATTRACT binary in $ATTRACTDIR='\"$ATTRACTDIR\"
  echo 'Please install ATTRACT following the installation instructions'
  echo 'ATTRACT is available at: http://www.attract.ph.tum.de/services/ATTRACT/attract.tgz'
  exit 1
fi
if [ ! -f $ATTRACTDIR/../version ] ||  [ `awk '{print ($1 < 0.4)}' $ATTRACTDIR/../version` -eq 1 ]; then
  echo 'Your ATTRACT version is too old to run this protocol. Please download and install the latest version of ATTRACT'
  echo 'ATTRACT is available at: http://www.attract.ph.tum.de/services/ATTRACT/attract.tgz'
  exit 1
fi
trap "kill -- -$BASHPID; attractclean" ERR EXIT
$ATTRACTDIR/shm-clean

rm -rf result.dat result.pdb result.lrmsd result.irmsd result.fnat result.interface >& /dev/null
function attractclean {
  $ATTRACTDIR/shm-clean
}

#name of the run
name=1AVX

#docking parameters
params="$ATTRACTDIR/../attract.par 1AVXAr.pdb 1AVXBr.pdb --fix-receptor"
scoreparams="$ATTRACTDIR/../attract.par 1AVXAr.pdb 1AVXBr.pdb --score --fix-receptor"

#grid parameters
gridparams=" --grid 1 receptorgrid.gridheader"

#parallelization parameters
parals="--np 4 --chunks 4"

#see if pypy is installed
PYPY=python
command -v pypy >/dev/null 2>&1 && PYPY=pypy

if [ 1 -eq 1 ]; then ### move and change to disable parts of the protocol

echo '**************************************************************'
echo 'Reduce partner PDBs...'
echo '**************************************************************'
cat unbound/1AVXA.pdb > 1AVXA.pdb
python $ATTRACTDIR/../allatom/aareduce.py 1AVXA.pdb 1AVXA-aa.pdb --chain A --dumppatch --pdb2pqr > 1AVXA.mapping
python $ATTRACTDIR/../allatom/aareduce.py 1AVXA-aa.pdb 1AVXA-heavy.pdb --heavy --chain A --readpatch  > /dev/null
python $ATTRACTTOOLS/reduce.py 1AVXA-aa.pdb 1AVXAr.pdb --chain A > /dev/null
cat unbound/1AVXB.pdb > 1AVXB.pdb
python $ATTRACTDIR/../allatom/aareduce.py 1AVXB.pdb 1AVXB-aa.pdb --chain B --dumppatch --pdb2pqr > 1AVXB.mapping
python $ATTRACTDIR/../allatom/aareduce.py 1AVXB-aa.pdb 1AVXB-heavy.pdb --heavy --chain B --readpatch  > /dev/null
python $ATTRACTTOOLS/reduce.py 1AVXB-aa.pdb 1AVXBr.pdb --chain B > /dev/null

echo '**************************************************************'
echo 'Reduce reference PDBs...'
echo '**************************************************************'
python $ATTRACTDIR/../allatom/aareduce.py bound/1AVXA.pdb refe-rmsd-1.pdb --heavy --pdb2pqr > /dev/null
python $ATTRACTDIR/../allatom/aareduce.py bound/1AVXB.pdb refe-rmsd-2.pdb --heavy --pdb2pqr > /dev/null

echo '**************************************************************'
echo 'Generate starting structures...'
echo '**************************************************************'
cat $ATTRACTDIR/../rotation.dat > rotation.dat
$ATTRACTDIR/translate 1AVXAr.pdb 1AVXBr.pdb > translate.dat
$ATTRACTDIR/systsearch > systsearch.dat
start=systsearch.dat

echo '**************************************************************'
echo 'calculate receptorgrid grid'
echo '**************************************************************'
awk '{print substr($0,58,2)}' 1AVXBr.pdb | sort -nu > receptorgrid.alphabet
$ATTRACTDIR/make-grid-omp 1AVXAr.pdb $ATTRACTDIR/../attract.par 5.0 7.0 receptorgrid.gridheader  --shm --alphabet receptorgrid.alphabet

echo '**************************************************************'
echo 'Docking'
echo '**************************************************************'

echo '**************************************************************'
echo '1st minimization'
echo '**************************************************************'
python $ATTRACTDIR/../protocols/attract.py $start $params $gridparams --vmax 1000 $parals --output out_$name.dat

echo '**************************************************************'
echo 'Final rescoring'
echo '**************************************************************'
python $ATTRACTDIR/../protocols/attract.py out_$name.dat $scoreparams --rcut 50.0 $parals --output out_$name.score

echo '**************************************************************'
echo 'Merge the scores with the structures'
echo '**************************************************************'
$PYPY $ATTRACTTOOLS/fill-energies.py out_$name.dat out_$name.score > out_$name-scored.dat

echo '**************************************************************'
echo 'Sort structures'
echo '**************************************************************'
$PYPY $ATTRACTTOOLS/sort.py out_$name-scored.dat > out_$name-sorted.dat

echo '**************************************************************'
echo 'Remove redundant structures'
echo '**************************************************************'
$ATTRACTDIR/deredundant out_$name-sorted.dat 2 | $PYPY $ATTRACTTOOLS/fill-deredundant.py /dev/stdin out_$name-sorted.dat > out_$name-sorted-dr.dat

echo '**************************************************************'
echo 'Sort structures'
echo '**************************************************************'
$PYPY $ATTRACTTOOLS/sort.py out_$name-sorted-dr.dat > out_$name-clustered-sorted.dat

echo '**************************************************************'
echo 'Soft-link the final results'
echo '**************************************************************'
ln -s out_$name-clustered-sorted.dat result.dat

echo '**************************************************************'
echo 'collect top 50 structures:'
echo '**************************************************************'
$ATTRACTTOOLS/top out_$name-clustered-sorted.dat 50 > out_$name-top50.dat
$ATTRACTDIR/collect out_$name-top50.dat 1AVXA-aa.pdb 1AVXB-aa.pdb > out_$name-top50.pdb
ln -s out_$name-top50.pdb result.pdb

echo '**************************************************************'
echo 'calculate backbone ligand RMSD'
echo '**************************************************************'
python $ATTRACTDIR/lrmsd.py out_$name-clustered-sorted.dat 1AVXB-heavy.pdb refe-rmsd-2.pdb --receptor 1AVXA-heavy.pdb > out_$name-clustered-sorted.lrmsd
ln -s out_$name-clustered-sorted.lrmsd result.lrmsd

echo '**************************************************************'
echo 'calculate backbone interface RMSD'
echo '**************************************************************'
python $ATTRACTDIR/irmsd.py out_$name-clustered-sorted.dat 1AVXA-heavy.pdb refe-rmsd-1.pdb 1AVXB-heavy.pdb refe-rmsd-2.pdb  > out_$name-clustered-sorted.irmsd
ln -s out_$name-clustered-sorted.irmsd result.irmsd

echo '**************************************************************'
echo 'calculate fraction of native contacts'
echo '**************************************************************'
python $ATTRACTDIR/fnat.py out_$name-clustered-sorted.dat 5 1AVXA-heavy.pdb refe-rmsd-1.pdb 1AVXB-heavy.pdb refe-rmsd-2.pdb > out_$name-clustered-sorted.fnat
ln -s out_$name-clustered-sorted.fnat result.fnat

attractclean

fi ### move to disable parts of the protocol

