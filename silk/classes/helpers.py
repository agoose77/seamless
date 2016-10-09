import numpy as np


def _prop_setter_any(child, value): return child.set(value)


def _prop_setter_json(child, value):
    return child.set(value, prop_setter=_prop_setter_json)


def _set_numpy_ele_prop(silkobj, prop, value):
    if value is None \
      and silkobj._has_optional:
        value = np.ma.masked

    pdtype = silkobj._data.dtype
    if not isinstance(prop, int):
        pdtype = pdtype[prop]
    if pdtype.kind in ('S', 'U'):
        itemsize1 = np.dtype(pdtype.kind+"1").itemsize
        maxlen = int(pdtype.itemsize / itemsize1)
        if pdtype.kind == 'S':
            if isinstance(value, bytes):
                pass
            else:
                value = str(value)
            if isinstance(value, str):
                value = value.encode('UTF-8')
        else: #'U'
            if not isinstance(value, str):
                value = str(value)
        if len(value) > maxlen:
            msg = "Length of string is %d, maximum length in \
numpy representation is %d"
            raise ValueError(msg % (len(value), maxlen))
        silkobj._data[prop] = value
    else:
        silkobj._data[prop] = value


def _set_numpy_ele_range(silkobj, start, end, value):
    assert end-start == len(value)
    p = silkobj._data
    backup_data = p[start:end]
    ok = False
    try:
        if p.dtype.kind in ('S', 'U'):
            for n in range(len(value)):
                _set_numpy_ele_prop(silkobj, start+n, value[n])
        else:
            p[start:end] = value
        ok = True
    finally:
        if not ok:
            p[start:end] = backup_data


def _get_numpy_ele_prop(silkobj, prop, length=None):
    d = silkobj._data
    if length is not None:
        d = d[:length]
    p = d[prop]
    if p.dtype.kind == "S":
        return bytes(p).decode()
    elif p.dtype.kind == "U":
        return str(p)
    else:
        return p