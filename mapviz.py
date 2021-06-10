from nested_lookup import nested_lookup
import pandas as pd
import IPython
from IPython.display import display, clear_output
from ipywidgets import HTML, Output, HBox
from ipyleaflet import Map, Marker, Popup

from search_dynamic import show_webpage,btn_new_search
from prepare_data import getJSON, avoidTupleInList, getYears
from widgets import createDropdown, createButton, createCheckBox

data = getJSON('data/records.json')
out = Output()

def show_map(data: list, by : str, first: bool):
    m = Map(
            center=(35.52437, -30.41053),
            zoom=2,
            close_popup_on_click=False
            )
    
    cities = {}
    marker = None
    for i in data:
            try :
                print(i[by])
                if i[by]["address"] not in cities:
                    city = i[by]["address"]
                    cities[city] = {}
                    cities[city]["message"] = "<b>"+ i["date"] + " </b> " + i["title"] + "<br><i>"+ i["contributor"] +"</i> <br> <a href=\""+ i["identifier"][1] + "\" target=\"_blank\">auf Kalliope</a> <hr>"
                    cities[city]["coordinates"] = [i[by]["coordinates"][1], i[by]["coordinates"][0]]
                    
                elif i[by]["address"] in cities:
                    city = i[by]["address"]
                    cities[city]["message"] = cities[city]["message"] + "<b>"+ i["date"] + " </b> " + i["title"] + "<br><i>"+ i["contributor"]  + "</i><br> <a href=\""+ i["identifier"][1] + "\" target=\"_blank\">auf Kalliope</a> <hr>"
            except : pass
    for i in cities.keys():
            try :
                message = HTML()
                if cities[i]["message"].count("<hr>") <3 :
                    message.value = cities[i]["message"]
                else : 
                    message.value = str(cities[i]["message"].count("<hr>")) + " Briefe. Es ist aber zu viele Ergebnisse, um alle hier zu zeigen."
                message.description = i.upper()
                marker = Marker(location=(cities[i]["coordinates"][0], cities[i]["coordinates"][1]))
                m.add_layer(marker)
                marker.popup = message
            except: pass
    if marker == None and first == True :
        show_map(data, "contributor_location", False)
    elif marker == None and first == False:
        print("An error has been encountered, the map cannot be displayed. We propose to have access to the results in a table format.")
        display(pd.DataFrame(pd.json_normalize(data)))
    else:
        print("Points on the map represent the " + by + " of letters.")
        display(m)


def an_change(change):
    if change['new'] == True :
        results = []
        for i in data:
            try :
                if 'Humboldt, Alexander' in i["subject"]:
                    results.append(i)
            except : 
                continue

        clear_output()
        an = createCheckBox("an AvH", True)
        von = createCheckBox("von AvH", False)

        display(HBox([an, von]))
        an.observe(an_change)
        von.observe(von_change)

        searching_by = ['Sender letters','Date']
        display(HBox([mapsearch(results, searching_by, True), btn_new_search()]))

    elif change['new'] == False:
        both_uncheck()


def von_change(change):
    if change['new'] == True :
        results = []
        for i in data:
            try :
                if 'Humboldt, Alexander' in i["creator"]:
                    results.append(i)
            except : 
                continue

        clear_output()
        an = createCheckBox("an AvH", False)
        von = createCheckBox("von AvH", True)
        display(HBox([an, von]))
        an.observe(an_change)
        von.observe(von_change)

        searching_by = ['Recipients letters','Date']
        display(HBox([mapsearch(results, searching_by, True), btn_new_search()]))

    elif change['new'] == False:
        both_uncheck()

def both_uncheck():
    clear_output()
    an = createCheckBox("an AvH", False)
    von = createCheckBox("von AvH", False)

    display(HBox([an, von]))

    an.observe(an_change)
    von.observe(von_change)
    show_map(data, "coverage_location", True)


def date_change(change): 
    if change['type'] == 'change' and change['name'] == 'value':
        date = change['new']
        results = []

        for i in data:
            try : 
                if change['new'] in i["date"]:
                    results.append(i)
            except: pass

        show_map(results, "coverage_location", True)

    if change['new'] == False:
        show_map(data, "coverage_location", True)

def by_date(data:dict):
    years = getYears(avoidTupleInList(nested_lookup('date', data)))
    dropdown = createDropdown('', years)
    dropdown.observe(date_change)
    return dropdown 

def is_male_name(name:str):
    male_name = ['Chr.', 'Jean-Baptiste', 'Heymann', 'Étienne', 'Whitelaw', 'Balduin', 'Edme', 'Hipolit', 'Moriz', 'Modest', 'Alire', 'Christ...', 'Dimitrij', 'Francois', 'Elte', 'Aylmer' ]
    for i in male_name:
        if name == i:
            return True


def mapsearch(data, search_possibilities, flag : bool):
    search_by = search_possibilities
    search_dropdown = createDropdown('Search by', search_by)
    new = flag
    
    def show_results(results):
        if len(results) <10:
            show_map(results, "coverage_location", True)
        else : 
            mapsearch(results, search_by, False)


    def change_creators(change):
        if change['type'] == 'change' and change['name'] == 'value':
            sender = change['new']
            results = []
            for r in data:
                try :
                    if r['creator'] == sender:
                        results.append(r)
                except : 
                    continue
            search_by.remove('Sender letters')
            show_map(results, "coverage_location", True)

    def change_recipients(change):
        if change['type'] == 'change' and change['name'] == 'value':
            recipients = change['new']
            results = []
            for r in data:
                try :
                    if r['subject'] == recipients:
                        results.append(r)
                except : 
                    continue
            search_by.remove('Recipients letters')
            show_results(results)

    def change_date(change):
        if change['type'] == 'change' and change['name'] == 'value':
            date = change['new']
            results = []
            for r in data:
                try :
                    if date in r['date']:
                        results.append(r)
                except : 
                    continue
            search_by.remove('Date')
            show_results(results)

    def no_element_for_dropdown(data, searching_by, element):
        search_by.remove(element)
        print('There is no {0} registered for these data.'.format(element.lower()))
        mapsearch(data, search_by, False)

    def change_search(change): 
        if change['type'] == 'change' and change['name'] == 'value':
            if change['new'] == 'Sender letters' and change['type'] == 'change':
                creators = avoidTupleInList(nested_lookup('creator', data))
                if len(creators) == 0:
                    return no_element_for_dropdown(data, search_by, change['new'] )
                else :
                    dropdown = createDropdown('Senders', creators)
                    dropdown.observe(change_creators) 
            elif change['new'] == 'Recipients letters' and change['type'] == 'change':
                recipients = avoidTupleInList(nested_lookup('subject', data))
                if len(recipients) == 0:
                    return no_element_for_dropdown(data, search_by, change['new'] )
                else :
                    dropdown = createDropdown('Recipients', recipients)
                    dropdown.observe(change_recipients)
            elif change['new'] == 'Date' and change['type'] == 'change':
                years = getYears(avoidTupleInList(nested_lookup('date', data)))
                if len(years) == 0:
                    return no_element_for_dropdown(data, search_by, change['new'] )
                else :
                    dropdown = createDropdown('Dates', years)
                    dropdown.observe(change_date)
            display(dropdown)
    
    search_dropdown.observe(change_search)
    if flag == True:
        return search_dropdown
    else :
        return display(search_dropdown)