import os
import requests
import operator
import re
import sys
sys.setrecursionlimit(10000)
from lib import ScraperManager

from flask import Flask, render_template, request, jsonify
from collections import Counter
from bs4 import BeautifulSoup
from rq import Queue
from rq.job import Job

from worker import conn

# Define App - import App from app
# from flask import Flask
App = Flask(__name__)
App.config.from_object(os.environ['APP_SETTINGS'])

q = Queue(connection=conn)

@App.route('/', methods=['GET', 'POST'])
def index():
    job_id = ""
    if request.method == 'POST':
        url = request.form['url']
        job = q.enqueue_call(
            func=scrape, args=(url,), result_ttl=5000
        )
        job_id = job.get_id()
        print(job_id)

    return render_template('index.html', job_id=job_id)

@App.route('/results/<job_key>', methods=['GET'])
def results_job_key(job_key):
    job = Job.fetch(job_key, connection=conn)

    if job.is_finished:
        print("made it here")
        # results = sorted(
        #     result.result.items()
        # )
        #
        # results = dict(results)
        master_data = job.result
    else:
        master_data =  "Nay!", 202
    # return render_template('results.html', master_data=master_data)
    return jsonify(master_data)

def scrape(url):
    # Get the url that they entered
    try:
        r = requests.get(url)
    except Exception as e:
        print("Unable to get URL: {}".format(e))
    # Process the HTML in the requst using BeautifulSoup
    if r:

        # Decode page encoding for our html content
        html = r.content.decode('ascii', 'ignore')

        # Pull decoded html into BeautifulSoup and then prettify() to fix any malformed html
        raw = BeautifulSoup(html, "lxml")
        clean_raw = raw.prettify()


        clean_raw_soup = BeautifulSoup(clean_raw,"lxml")



        # This is how we define sections (sections represents different groups of data we care about)
        section_identifier = 'bgcolor="#F2E3B8"'


        # This is how we define section field names
        field_identifier = 'strong'

        # This is how we identify our section field values
        field_value_identifier = 'font', {'color' : '#000000'}

        fields=[]
        section_fields=[]


        # Then we must break up our html into our data sections
        marked_raw = clean_raw.replace(section_identifier,"###!!! CHANGE ME !!!###")
        chunked_raw = marked_raw.split("###!!! CHANGE ME !!!###")
        # chunked_raw = chunked_raw[1:]
        # print(chunked_raw)
        # chunked_raw_as_string = ''.join(chunked_raw)
        # print(chunked_raw_as_string)
        # clean_raw_soup = BeautifulSoup(chunked_raw_as_string,"lxml")
        clean_raw_soup = str(clean_raw_soup).split(section_identifier,1)
        clean_raw_soup = clean_raw_soup[1]
        clean_raw_soup = BeautifulSoup(clean_raw_soup,"lxml")
        # Now lets get our list of section field values
        field_values = []
        section_field_values = []
        tagged_values = clean_raw_soup.find_all(field_value_identifier)
        # In each section of the html code we must search for our field names using our field_identifier
        for chunk in range(len(chunked_raw)):
            chunk = chunked_raw[chunk]

            section_content = BeautifulSoup(chunk,"lxml")
            section_field_identifiers = section_content.find_all(field_identifier)
            # Now that we've broken our section into chunks each containing our field_identifier,
            # we will format and sanatize our chunks to return a list of just our section field names
            for s_f_i in range(len(section_field_identifiers)):
                s_f_i = section_field_identifiers[s_f_i].text.strip()
                section_field = re.sub('[^a-zA-Z0-9-_*. ,]', '', s_f_i)
                if section_field != "":
                    fields.append(section_field)



            for tagged_value in range(len(tagged_values)):
                if 'strong' not in str(tagged_values[tagged_value]):
                    tagged_value = tagged_values[tagged_value].text.strip()
                    field_value = re.sub('[^a-zA-Z0-9-_*. ,]', '', tagged_value)
                    if field_value != "":
                        field_values.append(field_value)


            section_fields.append(fields)
            section_field_values.append(field_values)
            fields = []
            field_values = []
        # Now we have a list of fields that is divided by sections
        section_fields = section_fields
        section_field_values = section_field_values
        # print(section_fields)
        # print(len(section_fields))

        # Now we will grab/create the section names
        section_names = []

        tagged_sections = clean_raw_soup.find_all('td', {'bgcolor' : '#F2E3B8'})



        for t_s in range(len(tagged_sections)):
            # print(k.text)
            t_s = tagged_sections[t_s].text.strip()
            section_name = re.sub('[^a-zA-Z0-9-_*. ,]', '', t_s)
            if section_name != "":
                section_names.append(section_name)


        # Now we have a list of section names
        secion_names = section_names[1:]
        print(section_names)
        # print(len(section_names))





        # print(field_values)
        # print(len(field_values))


        # fields_and_values = dict(zip(section_fields, field_values))
        # print(section_fields)
        # print(len(section_fields))
        # print("########################")
        #
        # print(section_field_values)
        # print(len(section_field_values))
        # print("########################")
        # fields_and_values = {key:value for key, value in zip(section_fields,section_field_values)}
        #
        # # print(fields_and_values)
        # print(section_names)
        # print(len(section_names))
        # print("########################")

        # master_data = dict(zip(section_names, fields_and_values))
        master_data = {}
        main_data = {}

        print(len(section_fields),len(section_field_values),len(section_names))

        for pos,name in enumerate(section_names):
            # main_data[str(section_fields[pos])] = section_field_values[pos]

            master_data[name]=(section_fields[pos],section_field_values[pos])

        # master_data = {key:value for key, value in zip(section_names,fields_and_values)}


        print(master_data)
        # section_names_and_fields = dict(zip(section_names, section_fields))



        # for i in range(len(strong)):
        #     i = strong[i].text.strip()
        #     i = re.sub('[^a-zA-Z0-9-_*. ,]', '', i)
        #     if i != "":
        #         # print(i)
        #         fields.append(i)

        # print(fields)
        # print(master_data_sections)

        # for i,e in enumerate(tables):
        #     children = e.findChildren()
        #
        #     print("########################")
        #     print(children)
        #     print("########################")
            # table = str(e)
            # table_ends = table.split("</table>")
            # if len(table_ends) < 4:
            #     for section in master_data_sections:
            #         if section in table:
            #             content = str(tables[i+1])
            #             content_fields = BeautifulSoup(content,"lxml")
            #             fields = content_fields.find_all('strong')
            #             # print("#################")
            #             # print(section)
            #             # print("#################")
            #             # print(fields)
            #             section_data[str(section)]=fields

        # print(section_data)

        # for data in section_data:
        #     print(data)
        #     for field in section_data[data]:
        #         print(field)
        #         # print(type(field))
        #         if type(field) is str:
        #             print("########################")
        #         else:
        #         # print("#########")
        #
        #             field = field.text.strip()
        #             field = re.sub('[^a-zA-Z0-9-_*. ,]', '', field)
        #             if field != "":
        #                 # print(field)
        #                 fields.append(field)
        #             master_data[data] = fields
                # print(field)
                # print("#########")
        # print(master_data)
            # print(m.text)
            # m = str(m[0])
            # print(m)
            # print()
            # field = m.split(">")
            # field = field[1].split(">")
            # field = m.text.strip()
            # field = re.sub('[^a-zA-Z0-9-_*. ,]', '', field)
            # print(field)
            # fields.append(field)

        # print(fields)

        # print(section_data)
                        # print(tables[i+1])
        # for i,e in enumerate(tags):

        # for i,e in enumerate(tags):
        #
        #     d = str(e)
        #
        #     for field in owner_fields:
        #         if field in d:
        #             field_value = str(tags[i+1].text.strip())
        #             field_value = re.sub('[^a-zA-Z0-9-_*. ,]', '', field_value)
        #             owner_info[field] = field_value
        #     for field in site_fields:
        #         if field in d:
        #             field_value = str(tags[i+1].text.strip())
        #             field_value = re.sub('[^a-zA-Z0-9-_*. ,]', '', field_value)
        #             site_info[field] = field_value
        #
        # for sections in master_data_sections:
        #     master_data[sections] = eval(sections)

        return master_data

@App.route('/scrapers', methods=['GET'])
def scrapers_list():
    sm = ScraperManager(App)
    scrapers = sm.list_scrapers()
    return render_template('scrapers.html', scrapers=scrapers)

@App.route('/scrapers/<name>', methods=['GET'])
def scrapers_detail(name):
    sm = ScraperManager(App)
    scraper = sm.load_scraper(name)
    scraper.start()
    return render_template('scraper.html', scraper=scraper)

if __name__ == '__main__':
    App.run()
