# -*- coding: utf-8 -*-
"""
Created on Wed Apr 25 17:09:30 2018

@author: kouassi
Performance evaluation of test dataset prediction
"""

from sklearn.metrics import mean_squared_error as rmse1
import numpy as np
import xarray as xr
import numpy.core.numeric as _nx
from numpy.core.numeric import isnan
from numpy import isneginf, isposinf
from copy import copy
import matplotlib.pyplot as plt 
from scipy import fftpack


def mask_apply(y_true, y_final, amask):
    """ Application du masque pour travailler uniquement sur 
    le carré imputé par le réseau de neurone profond.
    y_true_m et y_final_m sont uniquement le carré ou la forme imputée 
    par le reseau de neurone profond. 
    y_true et y_pred sont le carré ou la forme imputée 
    par le reseau de neurone profond , entouré par zero pour le reste de l'imagette."""
    #nanval = -1e5
    # Réduction de dimension un array 2d (64*64)
    if amask.ndim>2:
        amask = np.squeeze(amask)
    if y_true.ndim>2:
        y_true = np.squeeze(y_true)
    if y_final.ndim>2:
        y_final = np.squeeze(y_final)
    # Définition et binarisation du masque
    amask = np.array(amask, dtype=int)
    # Application du masque sur les y_true et y_pred
    y_true = np.multiply(y_true, amask);
    y_pred = np.multiply(y_final, amask);
    y_true_m = y_true[y_true != 0]
    y_pred_m = y_pred[y_true != 0]
    return y_true, y_pred, y_true_m, y_pred_m

def mask_apply_crop(y_true, y_final, amask, cwidth=16, cheight=16, cb=True):
    """ Cette fonction est utilisée uniquement à l'étape d'évaluation des performances
    du réseau (Phase de Post-traitement).
    Cette fonction permet de selectionner les ytrue et ypred qu'on 
    veut selon la position dans l'image du carré dans l'image.
        - cheight : est la hauteur à prendre ou pas  en compte.
        - cwidth :  est la largeur à prendre ou pas en compte.
        - cb : booléen : if [True : crop extérieur] et [False : crop intérieur] """
    # Définition et binarisation du masque
    amask = np.array(amask, dtype=int)
    # Reduction de dimension de (64*64*1) à (64*64) si necessaire:
    if amask.ndim>2:
        amask = np.squeeze(amask)
    if y_true.ndim>2:
        y_true = np.squeeze(y_true)
    if y_final.ndim>2:
        y_final = np.squeeze(y_final)
    # Mask de selection des y true à plotter
    if (cb == True):
        bigmask = np.zeros(shape=(64,64))
        bigmask[cwidth:-cwidth, cheight:-cheight] = 1  
        amask = np.multiply(amask, bigmask)
    elif (cb == False):
        bigmask = np.ones(shape=(64,64))
        bigmask[cwidth:-cwidth, cheight:-cheight] = 0  
        amask = np.multiply(amask, bigmask)   
    # Application du masque sur 
    y_true = np.multiply(y_true, amask)
    y_final = np.multiply(y_final, amask)
    y_true_m = y_true[y_true != 0]
    y_final_m = y_final[y_true != 0]
    return y_true, y_final, y_true_m, y_final_m


def test_rmse(y_true, y_final, amask, dx=2, dy=0, cbool=True, cwidth=16, cheight=16 ):
    """ Calcul du loss par root mean square (sklearn) de la région completée uniquement: 
        - y_true and y_pred are numpy arrays
        - cbool = True: stands for using all values of the reconstructed area
        - cbool = False stands for using values of the validation area """
    if amask.ndim>2:
        amask = np.squeeze(amask);
    ytr, yfn, ytr_m, yfn_m = mask_apply(y_true,y_final, amask)
    if (dx==0 and dy==0):
        mseLoss = rmse1(ytr_m, yfn_m);
    elif (dx>0 or dy>0):
        if cbool == True:
            mseLoss = rmse1(np.multiply(ytr,amask), np.multiply(yfn,amask));
        elif cbool == False : 
            bigmask = np.zeros(shape=(64,64));
            bigmask[cwidth:-cwidth, cheight:-cheight] = 1;
            amask = np.multiply(amask,bigmask);
            isamask = amask[amask!=0]
            if (isamask.shape[0]>0):
                mseLoss = rmse1(ytr*amask, yfn*amask)
            elif (isamask.shape[0]==0):
                mseLoss= None            # Attention aux "None" dans l'exploitation des résultats?
    return mseLoss

def test_corrcoef(y_true,y_final,amask, bool1 =False):
    """calcul du coefficient de correlation entre chla predict et chla true 
    du carré imputé par le reseau de neurones profond.
    - y_true and y_pred are numpy arrays
    - bool = True: stands for using all values of the reconstructed area
    - bool = False stands for using values of the validation area """
    if bool1 == True:
        _, _, ytr_m, ypr_m = mask_apply(y_true, y_final, amask)
        CorrCoef = np.corrcoef(ytr_m, ypr_m, bias=True)[0][1]
    elif bool1 == False:
        _, _, ytr_mc, ypr_mc  = mask_apply_crop(y_true, y_final, amask, cwidth=16, cheight=16, cb=True)
        if ytr_mc.shape[0]>0:
            CorrCoef = np.corrcoef(ytr_mc, ypr_mc, bias=True)[0][1]
        elif ytr_mc.shape[0]==0:
            CorrCoef = None      # Attention aux "None" dans l'exploitation des résultats?
    return CorrCoef

def test_varratio(y_true,y_final, amask, bool1 =True):
    """calcul du rapport de variance entre chla predict et chla true 
    du carré imputé par le réseau de neurones profond.
    - y_true and y_pred are numpy arrays
    - cbool = True: stands for using all values of the reconstructed area
    - cbool = False stands for using values of the validation area """
    if bool1 == True:
        _, _, chlaTrm, chlaPrm = mask_apply(y_true, y_final,amask)
        vtm = np.var(chlaTrm, dtype=np.float64)
        vpm = np.var(chlaPrm, dtype=np.float64)
        VarRatio =  np.divide(vtm,vpm)
    elif bool1 == False:
        _, _, chlaTrmc, chlaPrmc  = mask_apply_crop(y_true, y_final, amask, cwidth=16, cheight=16, cb=True)
        if chlaTrmc.shape[0]>0:
            vtm = np.var(chlaTrmc, dtype=np.float64)
            vpm = np.var(chlaPrmc, dtype=np.float64)
            VarRatio = np.divide(vpm,vtm)
        if chlaTrmc.shape[0]==0:
            VarRatio = None      # Attention aux "None" dans l'exploitation des résultats?
            vpm = None; vtm = None
    return VarRatio, vpm, vtm


def test_pixel_masked_loss(y_true, y_final, amask):
    ytrue, yfinal, ytrue_m, yfinal_m = mask_apply(y_true,y_final, amask)
    i = np.where(ytrue != 0)
    index_dim = np.shape(i)
    i_center = int(index_dim[1]/2) # indice de l'indice central du mask
    b = np.subtract(ytrue, yfinal)
    # pixel central
    ix_center = i[0][i_center]
    iy_center = i[1][i_center]
    chla_center = b[ix_center,iy_center]
    # pixel central supérieur
    ix_up = i[0][0]
    #chla_upcenter = b[ix_up,iy_center]
    # pixel central inférieur
    ix_down = i[0][-1]
    #chla_DC = b[ix_down,iy_center]
    # pixel central gauche
    iy_left = i[1][0]
    #chla_LC = b[ix_center,iy_left]
    # pixel central droit
    iy_right = i[1][-1]
    #chla_RC = b[ix_center,iy_right]
    # pixel  des coins 
    chla_UL = b[ix_up,iy_left]       # coin supérieur gauche
    chla_UR = b[ix_up,iy_right]      # coin supérieur droit
    chla_DL = b[ix_down, iy_left]    # coin inférieur gauche
    chla_DR = b[ix_down, iy_right]   # coin inférieur droit 
    return chla_center, chla_UL, chla_UR, chla_DL, chla_DR

def azimuthalAverage(image, center=None):   
    """ This function comes from "radialProfile.py".
	Calculate the azimuthally averaged radial profile.
    image - The 2D image
    center - The [x,y] pixel coordinates used as the center. The default is 
             None, which then uses the center of the image (including 
             fractional pixels). """
    # Calculate the indices from the image
    A = np.indices(image.shape)
    y = A[0,:,:] ; x = A[1,:,:]
    if not center:
        center = np.array([(x.max()-x.min())/2.0, (x.max()-x.min())/2.0])
    r = np.hypot(x - center[0], y - center[1])
    # Get sorted radii
    ind = np.argsort(r.flat)
    r_sorted = r.flat[ind]
    i_sorted = image.flat[ind]
    # Get the integer part of the radii (bin size = 1)
    r_int = r_sorted.astype(int)
    # Find all pixels that fall within each radial bin.
    deltar = r_int[1:] - r_int[:-1]  # Assumes all radii represented
    rind = np.where(deltar)[0]       # location of changed radius
    nr = rind[1:] - rind[:-1]        # number of radius bin
    # Cumulative sum to figure out sums for each radius bin
    csim = np.cumsum(i_sorted, dtype=float)
    tbin = csim[rind[1:]] - csim[rind[:-1]]
    radial_prof = tbin / nr
    return radial_prof

def inpainted_region(outputTestName, y1='yfinal',nanval=-1e5, forspec=True):
    """ Cette fonction permet d'extraire la région à completer
    y1 = 'ypred'
    y1 = 'yfinal' 
    y1 = 'ytfull'
    forspec is a boolean used to specify if the computation is for spectrum computation 
    or not. In fact, spectrum computation needs the smallest rectangle area containing the inpainted region.
    whilst the display of the inpainted region shold the mere inpainted region.
    """
    #outputTestName = '../data/cloud/DatasetNN_cloud.nc'
    outputTest = xr.open_dataset(outputTestName)
    chla_true = outputTest.yt.values.squeeze()
    chla_X = outputTest.X.values.squeeze() 
    if y1 == 'ypred':
        chla_1 = outputTest.ypredict.values.squeeze()
    elif y1 == 'yfinal':
        chla_1 = outputTest.yfinal.values.squeeze()
    elif y1 == 'ytfull' : 
        chla_1 = outputTest.yfinal.values
    else:
        raise ValueError('y1 = ypred ou y1=yfinal ou y1=ytfull')
        
    CHLAFC = [] ; CHLATC=[]; Amask=np.array(outputTest.amask.values, dtype=int); #CHLATRFULL = np.empty_like(chla_X)     # initialisation
    for i in range(chla_1.shape[0]):
        #amask = np.equal(outputTest.yt[i].values.squeeze(),nanval) 
        amask = Amask[i,:,:]
        if forspec ==True:
            chla_F = chla_1[i,:,:] 
        elif forspec == False:
            chla_F = chla_1[i,:,:] 
            chla_F = np.multiply(amask,chla_F)
        else:
            print('forspec is a boolean')
        chla_T = chla_true[i,:,:]; #chla_x = chla_X[i,:,:]
        # Coordonnées des 4 extremités de la région contenant celle completée
        idx = np.argwhere(amask==1)
        ind_x_TL = np.argmin(idx[:,0], axis=0); x_TL = idx[ind_x_TL,0]
        ind_x_DR = np.argmax(idx[:,0], axis=0); x_DR = idx[ind_x_DR,0]
        ind_y_TL = np.argmin(idx[:,1], axis=0); y_TL = idx[ind_y_TL,1]
        ind_y_DR = np.argmax(idx[:,1], axis=0); y_DR = idx[ind_y_DR,1]
        # Calcul de la hauteur et de la largeur de cette région
        width  = 1 + np.subtract(y_DR, y_TL) 
        height = 1 + np.subtract(x_DR, x_TL) 
        # Reconstruction de la region contenant la region completée
        chlaFC = np.empty(shape=(height,width), dtype=float); chlaTC = copy(chlaFC)   # Initilisation
        chlaFC = chla_F[x_TL:x_TL+height, y_TL:y_TL+width]
        CHLAFC.append(chlaFC.tolist())
        chlaTC = chla_T[x_TL:x_TL+height, y_TL:y_TL+width]
        CHLATC.append(chlaTC.tolist()) 
    CHLATRFULL = np.add(np.multiply(np.logical_not(Amask),chla_X), np.multiply(Amask,chla_true))
    return CHLAFC, CHLATC, chla_1, CHLATRFULL

def power_spectrum(outputTestName,CHLATRFULL, cb=True,plot = True):
    """ cb : True if the spectrum is computed on the whole chla_final image
        cb : False if the sppectrum is computed only on the restricted area contianing 
             the inpainted image.
        plot = True enables the visualization of 20 images sampled randomly.
        plot = False disables the visualization of 20 images sampled randomly. """
    #outputTestName = '../data/cloud/DatasetNN_cloud.nc'
    PSD2D = [] ;PSD1D = []
    PSD2D_True = [] ;PSD1D_True = []
    if cb == True:
        outputTest = xr.open_dataset(outputTestName)
        chla_final = outputTest.yfinal.values.squeeze()
        for i in range(chla_final.shape[0]):
            chlaF = chla_final[i,:,:]
            chla_True = CHLATRFULL[i,:,:]
            # CALCUL DU SPECTRE DE PUISSANCE 
            # Take the fourier transform of the image.
            F1 = fftpack.fft2(chlaF)
            F1_True = fftpack.fft2(chla_True)
            # Now shift the quadrants around so that low spatial frequencies are in
            # the center of the 2D fourier transformed image.
            F2 = fftpack.fftshift(F1)
            F2_True = fftpack.fftshift(F1_True)
            # Calculate a 2D power spectrum
            psd2D = np.abs( F2 )**2
            PSD2D.append(psd2D.tolist())  # array contenant les a 2D power spectrum
            
            psd2D_True = np.abs( F2_True )**2
            PSD2D_True.append(psd2D.tolist())  # array contenant les a 2D power spectrum
            # Calculate the azimuthally averaged 1D power spectrum
            psd1D = azimuthalAverage(psd2D)
            PSD1D.append(psd1D.tolist())   
            psd1D_True = azimuthalAverage(psd2D_True)
            PSD1D_True.append(psd1D_True.tolist())             
        if plot == True:
            # Visualisation de 20 images tirées aléatoirement 
            nim = 1
            idx = np.random.randint(0,chla_final.shape[0], nim)
            for i,ind in enumerate(idx):
                fig, ax = plt.subplots()
                ax.imshow(np.log10(chla_final[ind,:,:]))
                ax.set_title("Inpainted Image",fontsize=14)
                
                fig, ax = plt.subplots()
                ax.imshow(np.log10(CHLATRFULL[ind,:,:]))
                ax.set_title("True Image",fontsize=14)
                
                fig, ax = plt.subplots()
                ax.imshow(np.log10(PSD2D[ind]))
                ax.set_title("Inpainted 2D Spectrum",fontsize=14)
                
                fig, ax = plt.subplots()
                ax.imshow(np.log10(PSD2D_True[ind]))
                ax.set_title("Inpainted 2D Spectrum",fontsize=14)

                fig, ax = plt.subplots()
                ax.plot(PSD1D[ind],label='Inpainted')
                ax.plot(PSD1D_True[ind],'r',label='True')
                ax.set_xscale('log', basex=2)
                ax.set_yscale('log', basey=2)
                ax.set_title("1D Spectrum",fontsize=14)
                ax.set(xlabel='Spatial Frequency', ylabel = "log2(power Spectrum)")
                ax.legend(loc='upper right')
                
    elif cb == False :   
        CHLAFC, CHLATC, chla_final, _ = inpainted_region(outputTestName, y1='yfinal',nanval=-1e5, forspec=True)
        for i in range(chla_final.shape[0]):
            chlaFC = np.array(CHLAFC[i])
            chlaTC = np.array(CHLATC[i])
            # CALCUL DU SPECTRE DE PUISSANCE 
            # Take the fourier transform of the image.
            F1 = fftpack.fft2(chlaFC)
            F1_True = fftpack.fft2(chlaTC)
            # Now shift the quadrants around so that low spatial frequencies are in
            # the center of the 2D fourier transformed image.
            F2 = fftpack.fftshift( F1 )
            F2_True = fftpack.fftshift( F1_True )
            # Calculate a 2D power spectrum
            psd2D = np.abs( F2 )**2
            PSD2D.append(psd2D.tolist())  # array contenant les a 2D power spectrum
            psd2D_True = np.abs( F2_True )**2
            PSD2D_True.append(psd2D_True.tolist())
            # array contenant les a 2D power spectrum            # Calculate the azimuthally averaged 1D power spectrum
            psd1D = azimuthalAverage(psd2D)
            PSD1D.append(psd1D.tolist())   
            psd1D_True = azimuthalAverage(psd2D_True)
            PSD1D_True.append(psd1D_True.tolist()) 
        if plot == True:
            # Visualisation de 20 images tirées aléatoirement 
            nim = 1
            idx = np.random.randint(0,chla_final.shape[0], nim)
            for i,ind in enumerate(idx):
                fig, ax = plt.subplots()
                ax.imshow(np.log10(CHLAFC[ind]))
                ax.set_title("Inpainted Image",fontsize=14)
                
                fig, ax = plt.subplots()
                ax.imshow(np.log10(CHLAFC[ind]))
                ax.set_title("True Image",fontsize=14)
                
                fig, ax = plt.subplots()
                ax.imshow(np.log10(np.array(PSD2D[ind])))
                ax.set_title("Inpainted 2D Spectrum",fontsize=14)
                
                fig, ax = plt.subplots()
                ax.imshow(np.log10(np.array(PSD2D_True[ind])))
                ax.set_title("Inpainted 2D Spectrum",fontsize=14)

                fig, ax = plt.subplots()
                ax.plot(PSD1D[ind],label='Inpainted')
                ax.plot(PSD1D_True[ind],'r',label='True')
                ax.set_xscale('log', basex=2)
                ax.set_yscale('log', basey=2)
                ax.set_title("1D Spectrum",fontsize=14)
                ax.set(xlabel='Spatial Frequency', ylabel = "log2(power Spectrum)")
                ax.legend(loc='upper right')
    else :
        print("cb est un booléen ! ")
    return PSD2D,PSD2D_True, PSD1D,PSD1D_True




def nan_to_nanval(x,nanval=-1e5):
    def getmaxmin(t):
        from numpy.core import getlimits
        f = getlimits.finfo(t)
        return f.max, f.min

    x = _nx.array(x, subok=True)
    xtype = x.dtype.type
    if not issubclass(xtype, _nx.inexact):
        return x
    iscomplex = issubclass(xtype, _nx.complexfloating)
    isscalar = (x.ndim == 0)
    x = x[None] if isscalar else x
    dest = (x.real, x.imag) if iscomplex else (x,)
    maxf, minf = getmaxmin(x.real.dtype)
    for d in dest:
        _nx.copyto(d, nanval, where=isnan(d))
        _nx.copyto(d, maxf, where=isposinf(d))
        _nx.copyto(d, minf, where=isneginf(d))
    return x[0] if isscalar else x

def mask_builder(testDataSet,maskBasename):
    #testDataSet = '../data/cloud/BaseTest_cloud.nc'
    #maskBaseName = '../data/cloud/maskTest_cloud.nc'
    ds = xr.open_dataset(testDataSet)
    am = np.array(ds.amask.values, dtype=float) 
    cm = np.array(ds.cmask.values, dtype=float) 
    nm = np.asarray(ds.amask.values, dtype=float)
    nm = np.add(am,cm); # Creation du masque
    nm[np.where(nm==1)] = 2
    nm[np.where(nm==0)] = 1
    nm[np.where(nm==2)] = 0 
    # remplacement des nan en nanval=-1e5 des yt (necessaire pour le recherche d'index)
    nanval = -1e5
    YT = ds['yt']; yt_values = copy(ds.yt.values); yt_values= nan_to_nanval(yt_values,nanval=nanval)
    YT.values = yt_values
    # Stockage dans une base de données
    AM = ds['amask']; AM.values = am;
    NM = ds['nmask']; NM.values = nm
    mds = xr.Dataset({'X':(['index','y','x'],ds.X),
                                       'yt':(['index','y','x'],YT),
                                       'amask':(['index','y','x'],AM),
                                       'nmask':(['index','y','x'],NM)},
                                        coords = ds.coords)  
    mds.to_netcdf(maskBasename)
    return mds

def index_search(ytrue,maskds):
    nanval = -1e5
    ytrue = nan_to_nanval(ytrue, nanval=nanval)
    count =0 ; ind11=None
    YT = maskds.yt.values; YTvalues=YT[count,:,:]
    # création d'un masque
    ytruem = ytrue[np.where(YTvalues!=nanval)]
    YTvaluesm = YTvalues[np.where(YTvalues!=nanval)]
    comp = np.array_equal(ytruem, YTvaluesm);
    if comp==True:
        ind11 = count 
    elif comp==False: 
        while (comp==False and count<-1+maskds.X.values.shape[0]):
            count+=1
            YTvalues=YT[count,:,:];
            YTvaluesm = YTvalues[np.where(YTvalues!=nanval)]
            ytruem = ytrue[np.where(YTvalues!=nanval)]
            comp = np.array_equal(ytruem, YTvaluesm)
            if comp == True:
                ind11 = copy(count)
                break
            print(count)
    ind1 = copy(ind11)
    return ind1