import sys
import os
import time
import cv2
import subprocess
import argparse
from pathlib import Path
import shutil
import colorama
colorama.init(autoreset=True)

# constants and utils

imageExtensions = [".png",".jpg", ".jpeg"]
videoExtensions = [".mp4",".gif"]

def run_cartoonize():
    subprocess.run([sys.executable, "-W ignore" , str(test_code / "cartoonize.py")], stdout=subprocess.PIPE)

def remove_folder_contents(folder):
    if folder.is_dir() == False:
        return
    for item in folder.iterdir():
        item.unlink()

# args
parser = argparse.ArgumentParser(description="Utility for https://github.com/SystemErrorWang/White-box-Cartoonization \n Put images and videos you want to cartoonize in \"test_code\\src\".")
parser.add_argument("path", help = "Path to test_code folder")
test_code = Path(parser.parse_args().path).resolve()

# get various paths
print ("Initializing...")
test_images = test_code / "test_images"
cartoonized_images = test_code / "cartoonized_images"
src = test_code / "src"
dst = test_code / "dst"

# checks
if test_code.name != "test_code":
    print(colorama.Fore.RED + "Path needs to be to the folder \"test_code\"")
    sys.exit(-1)

test_images.mkdir(parents=True, exist_ok = True)
cartoonized_images.mkdir(parents=True, exist_ok = True)

if len(list(test_images.iterdir())) != 0 or len(list(cartoonized_images.iterdir())) != 0:
    print(colorama.Fore.RED + "\"/test_images\" and \"/cartoonized_images\" needs to be empty!")
    sys.exit(-1)
    
src.mkdir(parents=True, exist_ok = True)
dst.mkdir(parents=True, exist_ok = True)

# file sorting
images = []
videos = []

for file in src.iterdir():
    if file.is_dir():
        continue
    suffix = file.suffix.lower()
    if suffix in imageExtensions:
        images.append(file)
    elif suffix in videoExtensions:
        videos.append(file)

print(f"Found {len(images)} images and {len(videos)} videos.")

# process images
if len(images):
    time.sleep(1)
    print("\n------------Processing images------------\n")
        
    try:
        print("Copying images from src...")
        for file in images:
            shutil.copy(file, test_images / (file.stem + "_cartoonized" + file.suffix) )

        print ("Running Cartoonize...")
        run_cartoonize()

        print("Copying results to dst")
        copied = 0
        for file in cartoonized_images.iterdir():
            newFile = dst/file.name
            if newFile.exists():
                continue
            shutil.copy(file, newFile)
            copied += 1
        if copied != 0:
            print (colorama.Fore.GREEN + str(copied) + " files copied")
        else:
            print (colorama.Fore.RED + "No files copied")
    finally:
        print ("Cleaning...")
        remove_folder_contents(test_images)
        remove_folder_contents(cartoonized_images)

# process videos
if len(videos):
    time.sleep(1)
    print("\n------------Processing videos------------\n")

    for i in range(0,len(videos)):
        s = f"[{i+1}/{len(videos)}] "
        file = videos[i]
        newFile = dst / (file.stem + "_cartoonized" + file.suffix)
        newVideo = None
        print (s + "Processing " + file.name + "...")
        
        if newFile.exists():
            print (colorama.Fore.RED + s + "File in \"/dst\" already exists!")
            continue

        try:
            print (s + "Spliting video...")
            video = cv2.VideoCapture(str(file))
            frameNr = 0
            while 1:
                ret, frame=video.read()
                if not ret:
                    break
                
                # we could use .png instead of .jpg to improve quality
                cv2.imwrite(str(test_images / ('{:04d}'.format(frameNr) + ".jpg")),frame)
                frameNr+=1
            print (s + "Split " + str(frameNr) + " frames.")

            print (s + "Running Cartoonize...")
            run_cartoonize()

            if frameNr == len(list(cartoonized_images.iterdir())):
                print (s + "Merging frames...")
                
                # creating new video writer with the same settings
                fourcc = int(video.get(cv2.CAP_PROP_FOURCC))
                fps = video.get(cv2.CAP_PROP_FPS)
                w = int(video.get(cv2.CAP_PROP_FRAME_WIDTH)) 
                h = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
                newVideo = cv2.VideoWriter(str(newFile), fourcc, fps, (w, h) )

                # writing all the frames to it
                for x in range(frameNr):
                    frame = cv2.imread(str(cartoonized_images / ('{:04d}'.format(x) + ".jpg")))
                    frame = cv2.resize(frame,(w,h)) # force frame to be of the correct size
                    newVideo.write( frame )
                    # cv2.imshow('video',frame)
                    # if cv2.waitKey(1) & 0xFF == ord('q'):
                    #     break

                # cv2.destroyWindows()

                print (s + "Merging audio... (not implmented)")
                ###

                print (colorama.Fore.GREEN + s + "Merging successful")
            else:
                print (colorama.Fore.RED + s + "Incorrect number of frames detected!")

        finally:
            print (s + "Cleaning...")
            video.release()
            if newVideo != None:
                newVideo.release()
            remove_folder_contents(test_images)
            remove_folder_contents(cartoonized_images)