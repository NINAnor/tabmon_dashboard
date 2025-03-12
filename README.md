# TABMON dashboard :star2:

Streamlit Dashboard summarizing the device deployment metadata for the [TABMON project](https://www.nina.no/english/TABMON).

The dashboard leverages `rclone` to serve the data and `.parquet` files and `duckdb` for optimising page refresh.

## How does this work

We serve the data that is stored in an S3 using `rclone serve`, the dashboard then connects to the bucket to fetch the `index.parquet` file containing all the bucket files' metadata. We specify the data path in `stack.env`.

Since we are connecting to a remote S3 bucket, we need `rclone` to access our credentials. It is possible to create a `secret` containing these credentials.

## Run the dashboard

```
docker compose up
```

## Acknowledgment

The dashboard has been developped by [Benjamin Cretois](mailto:benjamin.cretois@nina.no) and [Francesco Frassinelli](mailto:francesco.frassinelli@nina.no)
