# SoccerMon Dataset

This project utilizes the subjective monitoring data from the **SoccerMon** dataset.

## Dataset Details
- **Source**: Zenodo ([DOI: 10.5281/zenodo.10033832](https://zenodo.org/records/10033832))
- **Publication**: Midoglu, C. et al. *A large-scale multivariate soccer athlete health, performance, and position monitoring dataset.* Scientific Data 11, 576 (2024). [Nature Scientific Data](https://doi.org/10.1038/s41597-024-03386-x)
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)

## Dataset Structure
The dataset contains longitudinal data from two elite women's football teams over two full seasons (2020 and 2021). The subjective component (`subjective.zip`, ~706 KB) comprises:
1. **Training Load Reports**: Session duration, perceived exertion (RPE), activity types, session RPE (sRPE).
2. **Wellness Reports**: Daily self-reported metrics (1 to 10 scale) for fatigue, mood, readiness, sleep quality, sleep duration (hours), muscle soreness, and stress.
3. **Injury Reports**: Athlete-reported injury incidents, anatomical locations, and severity indicators.

## Automated Download
You can download and extract the dataset automatically by running:
```bash
python -m src.data_processing --download
```

## Manual Download Instructions
If downloading manually:
1. Visit https://zenodo.org/records/10033832
2. Download `subjective.zip` (~706 KB)
3. Extract the contents into `data/raw/` so that the directory contains the extracted player files or folders.
4. Run the data processing pipeline:
```bash
python -m src.data_processing
```
