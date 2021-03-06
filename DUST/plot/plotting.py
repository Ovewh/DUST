
import cartopy as cr
import cartopy.crs as ccrs

from matplotlib.offsetbox import AnchoredText
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates

from .utils import _gen_log_clevs, _gen_flexpart_colormap

import numpy as np
import xarray as xr



mpl.rcParams['axes.titlesize'] = 'x-large'
mpl.rcParams['axes.labelsize'] = 'large'
mpl.rcParams['xtick.labelsize'] = 'medium'
mpl.rcParams['ytick.labelsize'] = 'medium'
mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=["#825f87", "#5f34e7", "#d3494e", "#464196", "#017371", "#ff9a8a", "#fa2a55", "#13eac9"])
xr.set_options(keep_attrs=True)

def plot_emission_time_series(dset,
                                    title=None,
                                    ax = None,
                                    varName = None,
                                    auto_locator =False,
                                    **plot_kwargs):

    if isinstance(dset, xr.DataArray):
        dataarray=dset
    else:
        if varName == None:
            dataarray=dset[dset.varName]
        else:
            datarray=dset[varName]
    if ax == None:
        ax = plt.axes()

    xr.plot.plot(dataarray,ax=ax, **plot_kwargs)
    if title:
        title = ax.set_title(title)
    if auto_locator:
        locator = mdates.AutoDateLocator(minticks=5, maxticks=12)

        formatter = mdates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

    ax.grid(linestyle='-')

    return ax 
def plot_emission_sensitivity(dset,
                                var_Name=None,
                                ax=None,
                                plotting_method = 'pcolormesh',
                                mark_receptor = True,
                                info_loc = 'lower right',
                                log = True,
                                vmin = None,
                                vmax = None,
                                title=None,
                                projection =ccrs.PlateCarree(),
                                extent = None,
                                info_dict=None,
                                **kwargs):
    """
    DESCRIPTION
    ===========

        Main function for plotting flexpart emission sensitivity. Require a 2D data array 
        Subsetting and so one should instead be done by using xarray.

    USAGE
    =====

        fig, ax = dset.fp.plot_emssion_sensitivity(dset)

        optional arguments:
            point           : if xarray.dataset contains several receptor points
            plotting_method : either 'pcolormesh' or 'contourf' (default='pcolormesh')
            info_loc        : location of info_box, (default = 'lower right')
            log             : log colorscale True/False, (default = True)
            vmin            : lower bound of colorscale (default = None)
            vmax            : upper bound of colorscale (default = None)
            title           : plot title, if None default title is created.
            extent          : extent of the output map,if not already set, default
                                [70,120, 25, 50]

    """
    if ax == None:
        ax = plt.axes(projection=projection)
    if extent:
        ax.set_extent(extent)

    if var_Name==None:
        dataarray=dset[dset.varName]
    else:
        dataarray=dset[var_Name]
    
    mpl_base_map_plot_xr(dataarray, ax=ax,
                                plotting_method=plotting_method,
                                vmin=vmin, vmax=vmax, **kwargs
                                )
    if mark_receptor==True:
        ax.scatter(dset['RELLNG'], dset['RELLAT'], transform =projection, 
                marker='*', s=40, color='black', zorder=1000)
    
    if title:
        ax.set_title(title)
    else:
        ind_receptor = dset.attrs['ind_receptor']
        if ind_receptor == 1:
            title = 'Concentration'
        elif ind_receptor == 4:
            title = 'Dry depostion'
        elif ind_receptor == 3:
            title = 'Wet depostion'
        ax.set_title('FLEXPART {} simulation'.format(title))
    if info_dict:
        info_dict = info_dict
    else:
        info_dict = {
            'Version': dset.attrs['version'],
            'ldirect' : dset.attrs['ldirect']
        }


    create_info_str(ax, info_dict, info_loc)
    return ax


def create_info_str(ax,info_dict, loc):
    info_str = ''
    for key, item in info_dict.items():
        info_str = info_str + '{} : {}\n'.format(key,item) 

    anc_text = AnchoredText(info_str, loc=loc ,bbox_transform=ax.transAxes,prop=dict(size=8))
    ax.add_artist(anc_text)


def mpl_base_map_plot_xr(dataarray, ax=None,
                    plotting_method = 'pcolormesh',
                    log = True,
                    vmin = None,
                    vmax = None,
                    mark_receptor = False,
                    colorbar =True,
                    cmap = None,
                    projection=ccrs.PlateCarree(),
                    **kwargs):
    """
    DESCRIPTION
    ===========
        Backbone of DUST ploting functionally, should be as general as possible
        Data should be a 2D xarray.dataarray. This is mostly as simple wrapper of 
        xarray's matplotlib wrapper
    USAGE:
    ======
        dataarray : 2D xarray data array
        colorbar  : whether to draw colorbar or not, default =FALSE
        log : whether to plot logarithmic color scale.
        vmin 

    """

    attrs = dataarray.attrs
    if ax ==None:
        ax = plt.axes(projection=projection)


    if cmap == None:
        cmap = _gen_flexpart_colormap()
        cmap.set_over(color='k', alpha=0.8)
    if vmin  ==None and vmax == None:
        dat_min = dataarray.min()
        dat_max = dataarray.max()
    elif vmin != None and vmax == None:
        dat_min = vmin
        dat_max = dataarray.max()
    elif vmin == None and vmax != None:
        dat_min = dataarray.min()
        dat_max = vmax
        dataarray = xr.where(dataarray<vmax,dataarray,np.nan)
        dataarray.attrs = attrs
    else:
        dat_max = vmax
        dat_min = vmin
        
        dataarray = xr.where((dataarray > vmin), dataarray, np.nan)
        dataarray.attrs = attrs
    if log:
        levels = _gen_log_clevs(dat_min, dat_max)
        norm = mpl.colors.LogNorm(vmin=levels[0], vmax=levels[-1])
    else:
        levels = list(np.arange(dat_min, dat_max, (dat_max - dat_min) / 100))
        norm = None

    if plotting_method == 'pcolormesh':
        xr.plot.pcolormesh(dataarray,ax=ax, norm=norm, add_colorbar=colorbar,cmap=cmap,
                    **kwargs)

    elif plotting_method =='contourf':
        xr.plot.contourf(dataarray,ax=ax, norm=norm, add_colorbar=colorbar,cmap=cmap,
                    **kwargs)

    else:
        raise ValueError("`method` param '%s' is not a valid one." % plotting_method)

    return ax



    
