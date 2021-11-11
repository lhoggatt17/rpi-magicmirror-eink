#!/usr/bin/env python3
import asyncio
import logging
import tempfile
import argparse
import sys
import numpy as np
from aiocron import crontab
from pyppeteer import launch
from PIL import Image

# Import the waveshare folder (containing the waveshare display drivers) without refactoring it to a module

# find the lastest waveshare drivers here:
# https://github.com/waveshare/e-Paper/blob/master/RaspberryPi%26JetsonNano/python/lib/waveshare_epd/
sys.path.insert(0, './waveshare')
import epd7in5b


# Global config
display_width = 480		# Width of the display
display_height = 800		# Height of the display
is_portrait = False		# True of the display should be in landscape mode (make sure to adjust the width and height accordingly)
wait_to_load = 60		# Page load timeout
wait_after_load = 30		# Time to evaluate the JS afte the page load (f.e. to lazy-load the calendar data)
url = 'http://192.168.0.108:8088/'	# URL to create the screenshot of

black_threshold = 35            # if pixels have less than this much color (ie, are quite dim), make them black

def reset_screen():
    global display_width
    global display_height
    epd = epd7in5b.EPD()
    epd.init()
    epd.Clear()
    epd.sleep()


async def create_screenshot(file_path):
    global display_width
    global display_height
    global wait_to_load
    global wait_after_load
    global url
    global is_portrait
    logging.debug('Creating screenshot')
    browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox', '--headless', '--disable-gpu', '--disable-dev-shm-usage'], executablePath='/usr/bin/chromium-browser')
    page = await browser.newPage()
    if is_portrait:
        await page.setViewport({"width": display_width,"height": display_height})
    else:
        await page.setViewport({"width": display_height,"height": display_width})
    await page.goto(url, timeout=wait_to_load * 1000)
    await page.waitFor(wait_after_load * 1000);
    await page.screenshot({'path': file_path})
    await browser.close()
    logging.debug('Finished creating screenshot')


def get_images(image):

    global black_threshold

    red = (255,000,000)
    black = (000,000,000)
    white = (255,255,255)
    img = image.convert('RGB')
    data = np.array(img)
    data_w = data.copy()
    data_r = data.copy()
    
    # If the value of the pixel is less than black_threshold, make it black
    black_mask = np.bitwise_and(data[:,:,0] <= black_threshold, data[:,:,1] <= black_threshold, data[:,:,2] <= black_threshold)
    # If the R value is higher than the G or B value, make red (assumes simple coloring)
    red_mask = np.bitwise_or(data[:,:,0] > data[:,:,1], data[:,:,0] > data[:,:,2])
    # Everything else should be white
    white_mask = np.bitwise_not(np.bitwise_or(red_mask, black_mask))
    
    #make most things 'black' (use inverted colors)
    data_w[black_mask] = white
    data_r[black_mask] = white
    
    #make 'white' mask only for non-red lettering
    data_w[white_mask] = black
    data_w[red_mask] = white
    
    #make 'red' mask only for red lettering
    data_r[red_mask] = red
    data_r[white_mask] = white
    
    return Image.fromarray(data_w, mode='RGB'), Image.fromarray(data_r, mode='RGB')


def main():
    try:
        parser = argparse.ArgumentParser(description='Python EInk MagicMirror')
        parser.add_argument('-d', '--debug', action='store_true', dest='debug',
                            help='Enable debug logs.', default=False)
        parser.add_argument('-c', '--cron', action='store', dest='cron',
                            help='Sets a schedule using cron syntax')
        parser.add_argument('-r', '--reset', action='store_true', dest='reset',
                            help='Ignore all other settings and just reset the screen.', default=False)
        args = parser.parse_args()
        level = logging.DEBUG if args.debug else logging.INFO
        logging.basicConfig(level=level, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

	#save an image with the correct dimensions as 'yo.png' and put it in your project directory
        image = Image.open("yo.png") 
        image_w, image_r = get_images(image)
        
        # save black/white + black/red versions so you can tell what is going to make up the image
        image_w.save("yo_aliased_w.png")
        image_r.save("yo_aliased_r.png")
        
        logging.info('Initializing / waking screen.')
        epd = epd7in5b.EPD()
        epd.init()
        
        # takes about 18 seconds
        logging.info('Sending image to screen.')
        epd.display(epd.getbuffer(image_w), epd.getbuffer(image_r))
        
        # go to no-power state
        logging.info('Sending display back to sleep.')
        epd.sleep()
        logging.info('Refresh finished.')
         
    except KeyboardInterrupt:
        logging.info('Shutting down after receiving a keyboard interrupt.')
    finally:
        #logging.info('Resetting screen.')
        #reset_screen()
        pass


if __name__ == '__main__':
    main()
