# Web Crawling CafeF – Stock Dashboard
This project uses **Python + Streamlit + Plotly** to **collect and visualize stock data** from the website [CafeF](https://cafef.vn).
## Features
- Retrieve the opening price, closing price, highest price, lowest price, and trading volume of stocks.
- Display the data in a table and interactive line and bar charts using Plotly.
- Allow **selecting a time range**: from start date to end date.
- Automatically update the data daily (customizable).
## Installation 
#Clone the repository
git clone https://github.com/nguyenphuonghoangnhi/Web_crawling_CafeF.git
cd Web_crawling_CafeF
#Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate      
#Install required packages
pip install -r requirements.txt
## Usage
Run the Streamlit app: streamlit run crawler.py
## Notes
- Do not push `venv/` to GitHub.
- The project is designed for educational purpose.
## Acknowledgements
- CafeF for data source.
- Python libraries: streamlit, pandas, plotly, requests, schedule.
## Contact
For any questions or feedback, please contact:
- Email: [nguyenphuonghoangnhi26@gmail.com](mailto:nguyenphuonghoangnhi26@gmail.com)
- Linkedin: [Nhi Nguyen](https://www.linkedin.com/in/nhi-nguyen-ba52a42b5/)
