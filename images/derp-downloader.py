import os
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor
import warnings
from urllib3.exceptions import InsecureRequestWarning
import concurrent.futures

import time
# 경고 무시
warnings.simplefilter('ignore', InsecureRequestWarning)

# 설정
download_folders = ["twilight sparkle", "applejack", "fluttershy", "pinkie pie", "rainbow dash", "rarity", "princess celestia", "princess luna", "sunset shimmer", "derpy hooves", "maud pie", "starlight glimmer", "trixie"]
start_index = 300    # 시작 이미지 번호
# start_index = 186000    # 시작 이미지 번호
end_index = 40000     # 종료 이미지 번호
required_tags_list = [["twilight sparkle", "solo"], ["applejack", "solo"], ["fluttershy", "solo"], ["pinkie pie", "solo"], ["rainbow dash", "solo"], ["princess celestia", "solo"], ["princess luna", "solo"], ["sunset shimmer", "solo"], ["derpy hooves", "solo"], ["maud pie", "solo"], ["starlight glimmer", "solo"], ["trixie", "safe", "solo"]] # 포함 태그
banned_tags = []  # 거르는 태그 
upvote = 10

sleep_time = 7 # 5~6부터는 종종 막히는듯

def download_image(url, image_path):
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)

    response = session.get(url, verify=False)
    with open(image_path, "wb") as img:
        img.write(response.content)

def is_valid_image(image_tags, required_tags, banned_tags, upvote_count, min_upvotes=upvote):
    return all(tag in image_tags for tag in required_tags) and not any(tag in image_tags for tag in banned_tags) and upvote_count >= min_upvotes


def get_and_download_image(number, download_folders, required_tags_list, banned_tags):
    try:
        url = f"https://derpibooru.org/images/{number}"

        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        response = session.get(url, verify=False)

        soup = BeautifulSoup(response.text, "html.parser")
        
        # 태그 리스트 추출
        tagbox_content = soup.find(class_="block__content block__tagbox")
        tag_list_element = tagbox_content.find(class_="tag-list") if tagbox_content else None
        tags_elements = tag_list_element.find_all(class_="tag dropdown") if tag_list_element else []

        # 태그 이름 추출
        image_tags = [tag.get('data-tag-name') for tag in tags_elements]

        
       # 이미지 URL 확인 및 다운로드
        center_aligned = soup.find(class_="layout--center-aligned")
        wide_layout = center_aligned.find(class_="layout--wide") if center_aligned else None
        header_block = wide_layout.find(class_="block block__header") if wide_layout else None

        if header_block:
            flex_layout = header_block.find(class_="flex flex--wrap image-metabar center--layout")
            upvotes_layout = flex_layout.find_all(class_="stretched-mobile-links")[1]
            upvote_count = int(upvotes_layout.find(class_="upvotes").text.strip())

            stretched_links = flex_layout.find_all(class_="stretched-mobile-links")[3]
            a_tag= stretched_links.find_all("a")[2]
            
            overall_downloaded_flag=False
            
            if a_tag:
                image_url=a_tag["href"]

                for i in range(len(required_tags_list)):
                    downloaded_flag=False
                    required_tags=required_tags_list[i]
                    download_folder=download_folders[i]

                    if is_valid_image(image_tags ,required_tags,banned_tags ,upvote_count):
                        if image_url.endswith('.jpg'):
                            extension='.jpg'
                        elif image_url.endswith('.jpeg'):
                            extension='.jpeg'
                        elif image_url.endswith('.png'):
                            extension='.png'
                        else:
                            extension='.jpg'

                        image_path=os.path.join(download_folder,f"{download_folder}_{number}{extension}")
                        download_image(image_url,image_path)
                        
                        print(f"                        Downloaded: {number} - {download_folder}")
                        
                        downloaded_flag=True
                        overall_downloaded_flag=True
                    
                time.sleep(sleep_time)    
                
                if not overall_downloaded_flag:
                   print(f"Skipped: {number}")

    except Exception as e:
       print(f"An error occurred: {e}")

def download_images(download_folders, start_index, end_index, required_tags_list, banned_tags):
    # 폴더 생성
    for folder in download_folders: 
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    # 병렬
    with ThreadPoolExecutor() as executor:
        futures = []
        for i in range(start_index,end_index+1):
            futures.append(executor.submit(get_and_download_image,i ,download_folders ,required_tags_list,banned_tags))

        for future in concurrent.futures.as_completed(futures):
            pass

download_images(download_folders,start_index,end_index ,required_tags_list,banned_tags)