import json


def read_json_file(file_path):
    with open(file_path, 'r') as file:
        json_data = json.load(file)
    return json_data

#read the json file
file_path = './place.json'
restaurant_name = 'Yosemite National Park'
json_data = read_json_file(file_path)
print(json_data)

new_json_data = []

#clean the data
sum = 0
for i in range(len(json_data)):
    sum += json_data[i]['rating']
    new_json_data.append( {
        "rating": json_data[i]['rating'],
        "review": json_data[i]['snippet'],
        "likes": 0 if json_data[i]['likes'] == "" else json_data[i]['likes'],
        "user_reviews": 0 if json_data[i]['user.reviews'] == "" else json_data[i]['user.reviews'],
        "is_user_local_guide": 0 if json_data[i]['user.localGuide'] == "" else json_data[i]['user.localGuide'],
        "date": json_data[i]['date'], 
        "source": json_data[i]['source']
    })
average_rating = sum / len(json_data)

#organize the parent data   
parent_json = {
    "name": restaurant_name,
    "average_rating": average_rating,
    "reviews": new_json_data,
    "total_reviews": len(json_data)
}

#save the new json data
with open('cleaned_data.json', 'w') as file:
    json.dump(parent_json, file, indent=4)