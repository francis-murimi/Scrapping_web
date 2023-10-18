from flask import Flask ,render_template
from flask_sqlalchemy import SQLAlchemy
import requests
from bs4 import BeautifulSoup
import csv
from urllib.parse import urlparse  # Used to extract the domain from URLs

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///art_om.db'
db = SQLAlchemy(app)

class ScrapedLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), unique=True)
    scrapped = db.Column(db.Boolean, default=False)

def save_unique_scraped_link_to_db(url, scrapped):
    # Check if the link already exists in the database
    existing_link = ScrapedLink.query.filter_by(url=url).first()

    if not existing_link:
        new_link = ScrapedLink(url=url, scrapped=scrapped)
        db.session.add(new_link)
        db.session.commit()

def get_links_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for a successful response
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True)]

    return links

def scrape_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for a successful response
    except requests.exceptions.RequestException as e:
        print(f"Error scraping {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    # Extract the content you want from the page
    # You can modify this part according to your needs
    content = soup.get_text()

    return content

@app.route('/')
def index():
    return 'scrapper'

@app.route('/read_links')
def read_saved_links():
    saved_links = ScrapedLink.query.all()  # Retrieve all records from the ScrapedLink table
    
    return render_template('my_links.html', saved_links=saved_links)

@app.route('/scrape')
def scrape_and_save():
    url = "https://www.artofmanliness.com/2008/12/"  # Replace with the URL you want to scrape
    links = get_links_from_url(url)  # Use the function from the previous answer

    for link in links:
        save_unique_scraped_link_to_db(link, False)

    return 'Scraping and saving complete'

@app.route('/scrape_saved')
def scrape_saved_links():
    saved_links = ScrapedLink.query.all()

    for entry in saved_links:
        if not entry.scrapped and 'artofmanliness.com' in entry.url:
            links = get_links_from_url(entry.url)
        for link in links:
            save_unique_scraped_link_to_db(link, False)
        entry.scrapped = True
        db.session.commit()
            
            #content = scrape_content(link.url)
            #if content is not None:
                # Perform your action on the scraped content, e.g., save it to a file or process it
                # Once you've processed the link, mark it as "scrapped" in the database
                #link.scrapped = True
                #db.session.commit()

    return 'Scraping saved links complete'

# Function to save links to a CSV file
def save_links_to_csv(saved_links):
    # Define the filename for the CSV file
    csv_filename = 'art_of_manliness_links.csv'
    
    # Filter links with the domain 'www.artofmanliness.com'
    relevant_links = [link for link in saved_links if urlparse(link.url).hostname == 'www.artofmanliness.com']

    # Check if there are relevant links to save
    if relevant_links:
        # Open the CSV file for writing
        with open(csv_filename, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            
            # Write header row
            csv_writer.writerow(['ID', 'URL'])
            
            # Write data rows
            for link in relevant_links:
                csv_writer.writerow([link.id, link.url])

    return csv_filename

# Use this function in your route
@app.route('/save_art_of_manliness_links')
def save_art_of_manliness_links():
    saved_links = ScrapedLink.query.all()
    csv_filename = save_links_to_csv(saved_links)
    
    return f'Relevant links saved to {csv_filename}'

if __name__ == '__main__':
    with app.app_context():  # Create an application context
        db.create_all()  # Create the database tables
    app.run(debug=True)
