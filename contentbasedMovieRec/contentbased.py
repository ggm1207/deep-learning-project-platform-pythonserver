# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from ast import literal_eval
from sklearn.metrics import mean_squared_error
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import os, sys 


# 데이터셋 불러오기(MovieLens 100k)
df_ratings = pd.read_csv('./contentbasedMovieRec/ratings.csv')

# 평점 데이터셋 형태 확인
print("### Rating Dataset Format ###", end='\n\n')
print(df_ratings.head(), end='\n\n\n')
df_ratings.drop(['timestamp'], axis=1, inplace=True)


df_movies = pd.read_csv('./contentbasedMovieRec/movies.csv')

# 영화 데이터셋 형태 확인
print("### Movie Dataset Format ###", end = '\n\n')
print("Columns of Movie Dataset : ",df_movies.columns, end = '\n\n')
print(df_movies.head())

### Add Your Own Data ### 
# 모든 영화를 같은 평점을 주지 않도록 주의 #

###################################### Example #################################################
# User 800 is a HUGE fan of Harry Potter
rows = []                               # row = [user_id, movie_id, rating]
user_id = 800
rows.append([user_id, 1, 4])        # movie     1: Toy Story(1995)
rows.append([user_id, 4896, 4])     # movie  4896: Harry Potter and the Socerer's Stone 
rows.append([user_id, 5816, 5])     # movie  5896: Harry Potter and the Chamber of Secrets
rows.append([user_id, 69844, 5])    # movie 69844: Harry Potter and the Half-Blood Prince(2009)
rows.append([user_id, 12, 1])       # movie    12: Dracula: Dead and Loving It(1995)
rows.append([user_id, 177, 1])      # movie   177: Lord of Illusions(1995)
##################################################################################################
########################### Add Your Own Ratings using 'movie.csv' data #########################
# my_rows = []
# my_id = 2021
# rows.append([user_id, ,])       # Fill your movie id and rating     
# rows.append([user_id, ,])       # 여러분이 평가할 영화의 id와 점수를 입력하세요.
# rows.append([user_id, ,])

##################################################################################################
for row in rows:
    df_ratings = df_ratings.append(pd.Series(row, index=df_ratings.columns), ignore_index=True)
# print("df_ratings: ", df_ratings)

# Dataset의 User, Movie 수 확인
n_users = df_ratings.userId.unique().shape[0]
n_items = df_ratings.movieId.unique().shape[0]
# print("num users: {}, num items:{}".format(n_users, n_items))

movie_rate = dict()

for row in df_ratings.itertuples(index = False):
    user_id, movie_id, rate = row
    if movie_id not in movie_rate:
        movie_rate[movie_id] = [0, 0]
    # movie_rate[movie_id][0] += rate
    movie_rate[movie_id][1] += 1

for key, value in movie_rate.items():
    value1 = value[0] / value[1]
    movie_rate[key] = [round(value1, 3),value[1]]

# 데이터 전처리 
# user id, movie id의 범위를 (0 ~ 사용자 수 -1), (0 ~ 영화 수 -1) 사이로 맞춰줌.

user_dict = dict()      # {user_id : user_idx}, user_id : original data에서 부여된 user의 id, user_idx : 새로 부여할 user의 id
movie_dict = dict()     # {movie_id: movie_idx}, movie_id : original data에서 부여된 movie의 id, movie_idx: 새로 부여할 movie의 id
user_idx = 0
movie_idx = 0
ratings = np.zeros((n_users, n_items))
for row in df_ratings.itertuples(index=False):
    user_id, movie_id, _ = row
    if user_id not in user_dict:
        user_dict[user_id] = user_idx
        user_idx += 1
    if movie_id not in movie_dict:
        movie_dict[movie_id] = movie_idx
        movie_idx += 1
    ratings[user_dict[user_id], movie_dict[movie_id]] = row[2]
user_idx_to_id = {v: k for k, v in user_dict.items()}

movie_idx_to_name=dict()
movie_idx_to_genre=dict()
for row in df_movies.itertuples(index=False):
    movie_id, movie_name, movie_genre = row
    if movie_id not in movie_dict:              # 어떤 영화가 rating data에 없는 경우 skip
        continue
    movie_idx_to_name[movie_dict[movie_id]] = movie_name 
    movie_idx_to_genre[movie_dict[movie_id]] = movie_genre

df_movies['genres'] = df_movies['genres'].apply(lambda x : x.split('|')).apply(lambda x : " ".join(x))

df_movies

rates = dict()
rates['movieId'] = []
rates['score'] = []
rates['count'] = []
for key, value in movie_rate.items():
    rates['movieId'].append(key)
    rates['score'].append(value[0])
    rates['count'].append(value[1])

scores = pd.DataFrame(rates)
scores

df_movies = pd.merge(df_movies, scores, on='movieId')

df_movies.head(4)

tmp_m = df_movies['count'].quantile(0.89)
tmp_m

tmp_data = df_movies.copy().loc[df_movies['count'] >= tmp_m]
tmp_data.shape

del tmp_data

m = df_movies['count'].quantile(0.9)
data = df_movies.loc[df_movies['count'] >= m]

df_movies.head()

C = df_movies['score'].mean()

# print(C)
# print(m)

def weighted_rating(x, m=m, C=C):
    v = x['count']
    R = x['score']
    
    return ( v / (v+m) * R ) + (m / (m + v) * C)

df_movies['weighted_score'] = df_movies.apply(weighted_rating, axis = 1)

df_movies.head(4)

count_vector = CountVectorizer(ngram_range=(1, 3))
count_vector

c_vector_genres = count_vector.fit_transform(df_movies['genres'])
c_vector_genres

c_vector_genres.shape

#코사인 유사도를 구한 벡터를 미리 저장
gerne_c_sim = cosine_similarity(c_vector_genres, c_vector_genres).argsort()[:, ::-1]

gerne_c_sim.shape

def get_recommend_movie_list(df, movie_title, top=30):
    # 특정 영화와 비슷한 영화를 추천해야 하기 때문에 '특정 영화' 정보를 뽑아낸다.
    target_movie_index = df[df['title'] == movie_title].index.values
    
    #코사인 유사도 중 비슷한 코사인 유사도를 가진 정보를 뽑아낸다.
    sim_index = gerne_c_sim[target_movie_index, :top].reshape(-1)
    #본인을 제외
    sim_index = sim_index[sim_index != target_movie_index]

    #data frame으로 만들고 vote_count으로 정렬한 뒤 return
    result = df.iloc[sim_index].sort_values('weighted_score', ascending=False)[:20]
    return result

get_recommend_movie_list(df_movies, movie_title='Toy Story (1995)')

import requests
from urllib.request import urlopen
from PIL import Image

def movie_poster(titles):
    data_URL = 'http://www.omdbapi.com/?i=tt3896198&apikey=f9cdaffd'
    
    fig, axes = plt.subplots(2, 10, figsize=(30,9))
    
    for i, ax in enumerate(axes.flatten()):
        w_title = titles[i].strip().split()
        params = {
            's':titles[i],
            'type':'movie',
            'y':''    
        }
        response = requests.get(data_URL,params=params).json()
        
        if response["Response"] == 'True':
            poster_URL = response["Search"][0]["Poster"]
            img = Image.open(urlopen(poster_URL))
            ax.imshow(img)
            
        ax.axis("off")
        if len(w_title) >= 10:
            ax.set_title(f"{i+1}. {' '.join(w_title[:5])}\n{' '.join(w_title[5:10])}\n{' '.join(w_title[10:])}", fontsize=10)
        elif len(w_title) >= 5:
            ax.set_title(f"{i+1}. {' '.join(w_title[:5])}\n{' '.join(w_title[5:])}", fontsize=10)
        else:
            ax.set_title(f"{i+1}. {titles[i]}", fontsize=10)
        
    plt.show()

# rec2 = get_recommend_movie_list(df_movies, movie_title='Moana (2016)')
# rec2 = rec2['title'].apply(lambda x : x.split(' (')[0])
# movie_poster(list(rec2))


# 이미지를 읽어 결과를 반환하는 함수
def predict(title):
    rec2 = get_recommend_movie_list(df_movies, movie_title=title)
    rec2 = rec2['title'].apply(lambda x : x.split(' (')[0])
    return rec2.to_json(orient="split")

