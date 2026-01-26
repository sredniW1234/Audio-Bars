import colorama


class Bar:
    def __init__(
        self,
        name: str,
        total_length: int = 40,
        bar_offset: int = 0,
        internal_numbers: bool = False,
    ) -> None:
        """
        A simple progress bar for terminal display.

        :param name: The name of this audio bar.
        :type name: str
        :param total_length: The total length of the audio bar. This should account for name, percentage, etc.
        :type total_length: int
        :param bar_offset: How far from the name should the bar be? Note, this only adds padding and does not shift the bar over by x amount.
        :type bar_offset: int
        :param internal_numbers: Whether or not the percentage should be displayed within the brackets or not.
        :type internal_numbers: bool
        """
        self.name = name.ljust(bar_offset)
        self.total_length = total_length
        self.internal_numbers = internal_numbers

    def show(self, percent: float, ommit_print: bool = False, just: int = 0) -> str:
        """
        Displays the bar on the screen.

        :param percent: The percentage the bar should display
        :type percent: float
        :param ommit_print: Whether or not to actually print the bar.
        :type ommit_print: bool
        """
        percent = min(max(0, percent), 100) / 100

        def get_bars():
            max_bars = self.total_length - len(self.name) - 2
            bars = int(max_bars * percent)
            bars_to_show = list(("|" * bars).ljust(max_bars))

            # Green bars start at the beginning
            yellow_bars = int(max_bars * 0.5)
            red_bars = int(max_bars * 0.9)

            bars_to_show.insert(0, colorama.Fore.GREEN)  # green
            bars_to_show.insert(yellow_bars, colorama.Fore.YELLOW)
            bars_to_show.insert(red_bars, colorama.Fore.RED)
            bars_to_show.append(colorama.Fore.RESET)
            return "".join(bars_to_show)

        bar = (
            self.name
            + f"[{get_bars()}{(f' {str(int(percent*100)).rjust(2, "0").rjust(3)}%') if self.internal_numbers else ''}] {'' if self.internal_numbers else (str(int(percent*100)).ljust(2)+'%')}"
        ).ljust(just)

        if not ommit_print:
            print(bar, end="\r", flush=True)
        return bar


class MultiBar:
    def __init__(self, bars: list[Bar]) -> None:
        """
        A simple class that allows for multiple bars to be shown at a time.

        :param bars: A list of the bars to show
        :type bars: list[Bar]
        """
        self.bars = bars

    def show(self, percents: list[float], just: int = 0):
        """
        Docstring for show

        :param percents: The percentage each bar should be at. This must be the same length as the number of bars given when initialized.
        :type percents: list[float]
        """
        if len(percents) != len(self.bars):
            raise ValueError("Number of percents must match number of bars")

        for bar, percent in zip(self.bars, percents):
            bar = bar.show(percent, True, just)
            print(bar)

        print(f"\x1b[{len(self.bars)}A", end="")
