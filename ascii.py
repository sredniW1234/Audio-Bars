from PIL import Image
from PIL import ImageFilter
import numpy as np
from colorama import init, Fore
from os.path import exists


class AsciiImage:
    """
    Simple class to convert an image to colored ASCII art in the terminal.
    """

    def __init__(self, image: str | Image.Image) -> None:
        """
        Simple class to convert an image to colored ASCII art in the terminal.

        :param image_path: The path to the image file.
        :type image_path: str
        """
        self.image = None
        self.image_path = None
        if isinstance(image, Image.Image):
            self.Image = image
        else:
            self.image_path = image
        self.characters = " `.-':_,^=;><+!rc*/z?sLTv)J7(|Fi{C}fI31tlu[neoZ5Yxjya]2ESwqkP6h9d4VpOGbUAKXHm8RD#$Bg0MNWQ%&@"
        init(autoreset=True)

    def format_image(
        self, image: Image.Image, width: int, height: int = -1
    ) -> Image.Image:
        """
        Formats the image by resizing and sharpening. Maintains aspect ratio.

        :param image: The image object to format.
        :type image: Image.Image
        :param width: The desired width of the image.
        :type width: int
        :param height: The desired Height of the image. If set to -1, height will be auto_adjusted
        :type height: int
        :return: The formatted image.
        :rtype: Image
        """
        width = width
        if height == -1:
            height = int(image.height * (width / image.width))
        image = image.resize((width, height))
        image = image.filter(ImageFilter.SHARPEN)
        # image.quantize(len(characters), Image.Quantize.MAXCOVERAGE)
        return image

    def get_color_code(self, r, g, b) -> str:
        """
        Gets the AnSI escape code for the given RGB color.

        :param r: Desired red value (0-255)
        :param g: Desired green value (0-255)
        :param b: Desired blue value (0-255)
        :return: ANSI escape code for the specified RGB color.
        :rtype: str
        """
        return f"\033[38;2;{r};{g};{b}m"

    def ascii_image(self, width, square: bool, colored=False):
        """
        Prints the ASCII art to the terminal.

        :param width: The desired width of the ASCII art.
        """
        if self.image_path and not exists(self.image_path):
            return
        elif not self.image:
            return

        img = Image.open(self.image_path) if self.image_path else self.image
        img = self.format_image(img, width, width if square else -1)
        g_img = img.convert("L")  # Grayscale
        for y in range(g_img.height):
            for x in range(g_img.width):
                pixel = g_img.getpixel((x, y))
                rgb = img.getpixel((x, y))
                pixel = np.array(pixel) * len(self.characters) // 256
                if colored:
                    print(self.get_color_code(*rgb) + self.characters[pixel], end="")
                else:
                    print(self.characters[pixel], end="")
                print(self.characters[pixel], end="" + Fore.RESET)
            print()

    def ascii_image_str(self, width, square: bool, colored=False) -> list[str]:
        """
        Returns the ASCII art as a list of strings.

        :param width: The desired width of the ASCII art.
        """
        if self.image_path and not exists(self.image_path):
            return []
        elif not self.image:
            return []

        img = Image.open(self.image_path) if self.image_path else self.image
        img = self.format_image(img, width, width if square else -1)
        g_img = img.convert("L")  # Grayscale
        image_str = []
        for y in range(g_img.height):
            line = []
            for x in range(g_img.width):
                pixel = g_img.getpixel((x, y))
                rgb = img.getpixel((x, y))
                pixel = np.array(pixel) * len(self.characters) // 256
                if colored:
                    line.append(
                        self.get_color_code(*rgb)
                        + self.characters[pixel]
                        + self.characters[pixel]
                    )
                else:
                    line.append(self.characters[pixel] + self.characters[pixel])
            image_str.append("".join(line) + "\n" + Fore.RESET)
        return image_str
