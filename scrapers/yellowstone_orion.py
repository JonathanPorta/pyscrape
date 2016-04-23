from lib import Scraper as Scraper

class YellowstoneOrion(Scraper):
    def __init__(self, scraper_manager, name):
        print("YellowstoneOrion::init()")

        super().__init__(scraper_manager, name)
        self.scraper_manager = scraper_manager
        self.name = name

    def start(self):
        print("YellowstoneOrion::start()")
        super().start()
        
