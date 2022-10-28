import base64
import copy
import os
from pathlib import Path

import cv2
import numpy as np
from PIL import ImageGrab, Image

from geometry import Rectangle


def resource_path(relative):
    return os.path.join(
        os.environ.get("_MEIPASS",os.path.abspath(".")),
        relative
    )


def image_to_cv(img):
    res_ = resource_path(img)
    return cv2.imread(res_)


class ScreenImage:

    def __init__(self, rectangle: Rectangle):
        l_top, r_bot = rectangle.l_top, rectangle.r_bot
        screenshot = ImageGrab.grab(bbox=(l_top.x, l_top.y, rectangle.width, rectangle.height))  # x, y, w, h
        self.img_rgb = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2RGB)
        self.pillow_img = Image.fromarray(self.img_rgb)

    def find_on_screen(self, small_image, threshold=0.7):
        h, w = small_image.shape[:-1]
        res = cv2.matchTemplate(self.img_rgb, small_image, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)

        # only return rectangles that don't overlap each other
        all_rectangles = [Rectangle(x[0], x[1], w, h) for x in zip(*loc[::-1])]
        unique_rectangles = []
        for ar in all_rectangles:
            touches = False
            for ur in unique_rectangles:
                if ar.overlaps_with(ur):
                    touches = True
                    break
            if not touches:
                unique_rectangles.append(ar)

        return unique_rectangles

    def draw_rectangle_on_screen(self, rectangle_list, image_output='draw_result.png'):

        for rec in rectangle_list:
            pt = rec.l_top
            cv2.rectangle(self.img_rgb, (pt. x, pt.y), (pt.x + rec.width, pt.y + rec.height), (0, 0, 255), 1)

        cv2.imwrite(image_output, self.img_rgb)
