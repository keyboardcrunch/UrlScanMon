#!/usr/bin/python3

#
# Pulls table data from a Urlscan.io search and notifies on new findings
#

class ScanData(dict):
    def __init__(self):
        self = dict()

    def add(self, url, scan):
        self[url] = scan

def Mail(domain, content):
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import smtplib
    import ssl
    
    # Send mail
    message = MIMEMultipart()
    message["From"] = mailfrom
    message["To"] = mailto
    message["Subject"] = "UrlScanMon: New results for {}".format(domain)
    message.attach(MIMEText(content, "html"))
    messagedata = message.as_string()
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp, port, context=context) as server:
        server.login(mailfrom, mailpass)
        server.sendmail(mailfrom, mailto, messagedata)

def ScrapeData(site):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.firefox.options import Options

    # Settings
    results = ScanData()
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    driver.implicitly_wait(10)
    driver.get(site)

    # Scrape scan data
    table = driver.find_element_by_xpath("/html/body/div[2]/div/div[3]/div/table/tbody")
    rows = table.find_elements(By.TAG_NAME, "tr")
    for row in rows:
        col = row.find_elements(By.TAG_NAME, "td")[1]
        href = col.find_elements(By.TAG_NAME, "a")[0]
        url = href.text
        scan = href.get_attribute("href")
        #print("{}\n{}\r\n".format(url, scan))
        results.add(url, scan)
    driver.quit()
    return results

def QueryString(string, history_file, notification):
    site = "https://urlscan.io/search/#filename%3A" + string
    results = ScrapeData(site)    
    new_scans = ScanData()
    body = """\
    <html>
        <body>
            <h1>Urlscan Monitor: Results for {}</h1>
            <ul>
    """.format(string)
    footer = """\
            </ul>
        </body>
    </html>
    """
    if not os.path.exists(history_file): # Write history file and Notify
        with open(history_file, 'a', newline='') as h:
            writer = csv.writer(h)
            for url, scan in results.items():
                body += '<li><a href="{}">{}</a></li>\r\n'.format(scan, url)
                writer.writerow([url,scan])
                new_scans.add(url,scan)
        body += footer

    else: # load history.csv and only notify new domains
        scan_history = ScanData()
        with open(history_file) as h:
            reader = csv.reader(h)
            for row in reader:
                scan_history.add(row[0],row[1])
        with open(history_file, 'a', newline='') as hf:
            writer = csv.writer(hf)
            for url, scan in results.items():
                if not url in scan_history.keys():
                    new_scans.add(url,scan)
                    body += '<li><a href="{}">{}</a></li>\r\n'.format(scan, url)
                    writer.writerow([url,scan])
        body += footer

    # Send notifications
    if bool(new_scans):
        if notification == "mail":
            Mail(string, body)
        else:
            print(string)
            for url, scan in new_scans.items():
                print("\t{} - {}".format(url,scan))
    else:
        print("No new findings.")



if __name__ == "__main__":
    import os
    import sys
    import csv
    
    # Paths
    history_path = os.path.join(os.getcwd(), "history")
    if not os.path.exists(history_path):
        os.mkdir(history_path)
    string_file = os.path.join(os.getcwd(), "strings.txt")
    if not os.path.exists(string_file):
        print("strings.txt is missing")
        sys.exit(1)

    # Notify settings
    notification = "none" # options: mail, none
    mailto = ""
    mailfrom = ""
    mailpass = ""
    smtp = ""
    port = "465"

    # Process strings.txt
    strings = open(string_file, 'r').readlines()
    for string in strings:
        string = string.strip()
        history_file = os.path.join(history_path, "{}.csv".format(string))
        if not string == "":
            QueryString(string, history_file, notification)
