from preprocess_func.audio_preprocessing import preprocess_all_device_stats, preprocess_dataset_stats
from preprocess_func.site_preprocessing import preprocess_sites

def main(parquet_file, username, password, base_dir):
    preprocess_dataset_stats(parquet_file, username, password)
    preprocess_all_device_stats(parquet_file, username, password)
    preprocess_sites(parquet_file, username, password, base_dir)


if __name__ == "__main__":

    main(parquet_file = "https://tabmon.nina.no/data/index.parquet",
         username="test", 
         password="test", 
         base_dir = "http://rclone:8081/data")
