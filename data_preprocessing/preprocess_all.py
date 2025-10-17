from preprocess_func.audio_preprocessing import preprocess_all_device_stats, preprocess_dataset_stats
from preprocess_func.site_preprocessing import preprocess_sites
from preprocess_func.device_status_preprocessing import main_status
from preprocess_func.preprocess_heatmap import preprocess_heatmap

def main(parquet_file, username, password, base_dir, site_csv):
    preprocess_dataset_stats(parquet_file, username, password)
    preprocess_all_device_stats(parquet_file, username, password)
    preprocess_sites(parquet_file, username, password, base_dir)
    main_status(parquet_file, site_csv, username=username, password=password)
    preprocess_heatmap(parquet_file, site_csv, username=username, password=password)

if __name__ == "__main__":

    main(parquet_file = "https://tabmon.nina.no/data/index.parquet",
         username="test", 
         password="test", 
         base_dir = "http://rclone:8081/data",
         site_csv="https://tabmon.nina.no/data/site_info.csv")
