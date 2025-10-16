#!/bin/bash

rclone copy ./all_device_stats.csv nirds3:bencretois-ns8129k-proj-tabmon/data/preprocessed/
rclone copy ./dataset_stats.csv nirds3:bencretois-ns8129k-proj-tabmon/data/preprocessed/