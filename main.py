#!/usr/bin/env python3
import asyncio
import logging
from logging.handlers import RotatingFileHandler
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
    logging.info('Creating screenshot')
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


async def refresh():
    logging.info('Starting refresh.')
    logging.debug('Initializing / waking screen.')
    epd = epd7in5b.EPD()
    epd.init()
    with tempfile.NamedTemporaryFile(suffix='.png') as tmp_file:
        logging.info(f'Created temporary file at {tmp_file.name}.')
        await create_screenshot(tmp_file.name)
        logging.debug('Opening screenshot.')
        image = Image.open(tmp_file)
        # Replace all colors with are neither black nor red with white
        image_w, image_r = get_images(image)
        # Rotate the image by 90°
        if is_portrait:
           logging.debug('Rotating image (portrait mode).')
           image = image.rotate(90)
        logging.debug('Sending image to screen.')
        epd.display(epd.getbuffer(image_w), epd.getbuffer(image_r))
    logging.debug('Sending display back to sleep.')
    epd.sleep()
    logging.info('Refresh finished.')


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
        
        logFile = '/home/pi/Documents/rpi-magicmirror-eink/eInk-refresher.log'
        rfh = RotatingFileHandler(
	    filename=logFile, 
	    mode='a',
	    maxBytes=10*1024*1024,
	    backupCount=2,
	    encoding=None,
	    delay=0
	)
        
        logging.basicConfig(
		level=level, 
		format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
		handlers=[rfh, logging.StreamHandler(sys.stdout)]
        )
        

        if not args.reset:
            if args.cron:
                logging.info(f'Scheduling the refresh using the schedule "{args.cron}".')
                crontab(args.cron, func=refresh)
                # Initially refresh the display before relying on the schedule
                asyncio.get_event_loop().run_until_complete(refresh())
                asyncio.get_event_loop().run_forever()
            else:
                logging.info('Only running the refresh once.')
                asyncio.get_event_loop().run_until_complete(refresh())
    except KeyboardInterrupt:
        logging.info('Shutting down after receiving a keyboard interrupt.')


if __name__ == '__main__':
    main()
