#!/usr/bin/env python
import numpy as np
import xarray as xr
import argparse as ap
import DUST
import os
from DUST.process_data_dust import process_per_pointspec, process_per_timestep, create_output
import pandas as pd
from IPython import embed
"""
AUTHOR
======
    Ove Haugvaldstad

    ovehaugv@outlook.com

"""

if __name__ == "__main__":
    parser = ap.ArgumentParser(description="""Multiply FLEXPART emissions sensitivities with modelled dust emissions from FLEXDUST,
        and save the output to a new NETCDF file file.""")
    parser.add_argument('path_flexpart', help='path to flexpart output')
    parser.add_argument('path_flexdust', help='path to flexdust output')
    parser.add_argument('--outpath', '--op', help='path to where output should be stored', default='./out')
    parser.add_argument('--x0' ,help = 'longitude of lower left corner of grid slice', default=None, type=int)
    parser.add_argument('--y0', help='latitude of lower left corner of grid slice', default=None, type=int)
    parser.add_argument('--x1', help='longitude of top right corner of grid slice', default=None, type=int)
    parser.add_argument('--y1', help='latidute of top right corner of grid slice', default=None, type=int)
    parser.add_argument('--height', help='height of lowest outgrid height', default=None, type=int)
    args = parser.parse_args()

    pathflexpart = args.path_flexpart
    pathflexdust = args.path_flexdust
    outpath = args.outpath
    x0 = args.x0
    x1 = args.x1
    y1 = args.y1
    y0 = args.y0
    height = args.height
    
    flexdust_ds = DUST.read_flexdust_output(pathflexdust)['dset']
    flexdust_ds = flexdust_ds.sel(lon=slice(x0,x1), lat=slice(y0,y1))
    # Check whether output is per time step or per release?
    ds = xr.open_dataset(pathflexpart)
    if 'pointspec' in ds.dims:
        print('per receptor point')
        ds, out_data, surface_sensitivity = process_per_pointspec(ds, flexdust_ds, x0, x1, y0, y1, height=height)
        ds.attrs['relcom'] = str(ds.RELCOM[0].values.astype('U35')).strip().split(' ')[1:]

    else:
        print('per timestep')
        ds, out_data, surface_sensitivity = process_per_timestep(ds, flexdust_ds, x0, x1, y0, y1, height=height) 
    
    out_ds = create_output(out_data,surface_sensitivity,ds)
    
    flexdust_ds.close()
    ds.close()
    spec_com = ds.spec001_mr.attrs['long_name']
    f_name = out_ds.attrs['varName']
    shape_dset = out_ds[f_name].shape
    encoding = {'zlib':True, 'complevel':9, 'chunksizes' : (1,10, shape_dset[2], shape_dset[3]),
    'fletcher32' : False,'contiguous': False, 'shuffle' : False}
    outFile_name = os.path.join(outpath,out_ds.attrs['filename'])
    print('writing to {}'.format(outFile_name))
    out_ds.to_netcdf(outFile_name, encoding={f_name:encoding, 'surface_sensitivity':encoding})
 
