from seamless import macro, editor
from seamless.core.cell import Cell

@macro("str")
def filelink(ctx, cell_type):
    pinparams = {
       "inp": {
         "pin": "input",
         "dtype": cell_type
       },
       "filepath" : {
         "pin": "input",
         "dtype": "str"
       },
       "latency" : {
         "pin": "input",
         "dtype": "float"
       },
       "outp": {
         "pin": "output",
         "dtype": cell_type
       },
    }
    ed = ctx.ed = editor(pinparams)
    ed.code_start.cell().fromfile("cell-filelink-start.py")
    ed.code_update.cell().set("write_file()")
    ed.code_stop.cell().set('t.join(0)')
    ctx.export(ed)

def link(cell, directory, filename, latency=0.2, solid=True, own=False):
    import os
    assert isinstance(cell, Cell)
    assert cell.context is not None
    filepath = os.path.join(directory, filename)
    fl = filelink(cell.dtype)
    fl.filepath.cell().set(filepath)
    fl.latency.cell().set(latency)
    cell.connect(fl.inp)
    if solid:
        fl.outp.solid.connect(cell)
    else:
        fl.outp.liquid.connect(cell)
    if own:
        cell.own(fl)
    fl._validate_path()
    return fl
