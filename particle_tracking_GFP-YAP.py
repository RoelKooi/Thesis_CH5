# -*- coding: utf-8 -*-
"""
Created on Thu Jan 16 10:04:53 2025

@author: 20201634
"""

import matplotlib
import matplotlib.pyplot as plt
import os

import numpy as np
import pandas as pd
from pandas import DataFrame, Series

import pims
import cv2
import trackpy as tp
import re

def main():
    data = pd.read_csv("D:/A2F4_MCF10a/Cilia_Ctrl/20250117_SegmentShapeDivideByIntensityNuclei.csv")
    
    # Split the control and actuated data from the main set
    ctrl = data[data['Metadata_Condition']=="Cilia_Ctrl"]
    act = data[data['Metadata_Condition']=="Cilia_Actuated"]
    
    link_ctrl = tp.link(ctrl, 30,
                        pos_columns=['Location_Center_Y', 'Location_Center_X'],
                        t_column='Metadata_FrameNo',
                        memory=1
                        )
    
    link_act = tp.link(act, 30,
                       pos_columns=['Location_Center_Y', 'Location_Center_X'],
                       t_column='Metadata_FrameNo',
                       memory=1
                       )
    
    filt_ctrl = tp.filter_stubs(link_ctrl.rename(columns={"Metadata_FrameNo": "frame"}), 20)
    filt_act = tp.filter_stubs(link_act.rename(columns={"Metadata_FrameNo": "frame"}), 20)
    
    link_ctrl.to_csv("D:/A2F4_MCF10a/Tracking/CTRL_linked_30_20250118.csv")
    link_act.to_csv("D:/A2F4_MCF10a/Tracking/ACT_linked_30_20250118.csv")
    filt_ctrl.to_csv("D:/A2F4_MCF10a/Tracking/CTRL_filtered_20_20250118.csv")
    filt_act.to_csv("D:/A2F4_MCF10a/Tracking/ACT_filtered_20_20250118.csv")
    
    

def old_data_process():
    imno_pattern = 'image_(?P<ImNo>[0-9]{1,3}).tif$'
    folder = "D:/A2F4_MCF10a/Tracking/No_act"
    # Read data
    raw_act = pd.read_csv('D:/A2F4_MCF10a/Cilia_Actuated/20240913_YAPintensity_at_nuclei_ACT_Nuclei.csv')
    raw_ctrl = pd.read_csv("D:/A2F4_MCF10a/Cilia_Ctrl/20240913_YAPintensity_at_nuclei_CTRL_Nuclei.csv")
    
    data_ctrl_img = pd.read_csv("D:/A2F4_MCF10a/Cilia_Ctrl/20240913_YAPintensity_at_nuclei_CTRL_Image.csv")
    data_act_img = pd.read_csv("D:/A2F4_MCF10a/Cilia_Actuated/20240913_YAPintensity_at_nuclei_ACT_Image.csv")
    
    # data_ctrl = raw_ctrl.join(data_ctrl_img, on="ImageNumber", how='left', rsuffix='_FromImage')
    data_ctrl = pd.merge(raw_ctrl, data_ctrl_img, on='ImageNumber', how='left')
    # data_act = raw_act.join(data_act_img, on="ImageNumber", how='left', rsuffix='_FromImage')
    data_act = pd.merge(raw_act, data_act_img, on='ImageNumber', how='left')
    
    
    
    ctrl_fr_n = [int(re.match(imno_pattern, s).group("ImNo")) for s in data_ctrl['FileName_YAP']]
    act_fr_n = [int(re.match(imno_pattern, s).group("ImNo")) for s in data_act['FileName_YAP']]
    
    data_ctrl['frame'] = ctrl_fr_n
    data_act['frame'] = act_fr_n
    
    link_ctrl = tp.link(data_ctrl, 30,
                        pos_columns=['Location_Center_Y', 'Location_Center_X'],
                        t_column='frame',
                        memory=3
                        )
    link_act = tp.link(data_act, 30,
                       pos_columns=['Location_Center_Y', 'Location_Center_X'],
                       t_column='frame',
                       memory=3
                       )
    
    filt_ctrl = tp.filter_stubs(link_ctrl, 20)
    filt_act = tp.filter_stubs(link_act, 20)
    
    link_ctrl.to_csv("D:/A2F4_MCF10a/Tracking/CTRL_linked_30_ordered.csv")
    link_act.to_csv("D:/A2F4_MCF10a/Tracking/ACT_linked_30_ordered.csv")
    filt_ctrl.to_csv("D:/A2F4_MCF10a/Tracking/CTRL_filtered_20_ordered.csv")
    filt_act.to_csv("D:/A2F4_MCF10a/Tracking/ACT_filtered_20_ordered.csv")
    

def make_img_seq(folder, ftype='png'):
    return pims.ImageSequence(folder+"/*."+ftype)

def track(folder, ftype="png", invert=True, min_traj=0):
    frames = make_img_seq(folder, ftype=ftype)
    f = tp.batch(frames[:], 5, invert=invert)
    t = tp.link(f, 5, memory=3)
    t_filt = tp.filter_stubs(t, min_traj)
    return f, t_filt

def n_traject(df, df_filt, min_traj, success_frac):
    return df_filt['particle'].nunique() <= success_frac * df['particle'].nunique()

def median(df, df_filt, min_traj, success_frac):
    tl_df = traj_lengths(df)
    tl_filt = traj_lengths(df_filt)
    return np.median(tl_filt) >= min_traj

def traj_lengths(df):
    result = []
    for i in range(df['particle'].nunique()):
        result.append(len(df[df['particle']==i]))
    return result

def optimise_step_dist(df, guess=5, min_traj=40, max_guess=100, success_frac=.9, method=n_traject):
    while guess <= max_guess:
        t = tp.link(df, guess, memory=3)
        filt = tp.filter_stubs(t, min_traj)
        if method(t, filt, min_traj, success_frac): # i.e. if a fraction of success_frac of original linked data survive the filter 
            break
        guess += 1
    return filt, guess


if __name__ == "__main__":
    main()
