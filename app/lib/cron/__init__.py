from app.config.cplog import CPLog
from app.lib.cron.eta import startEtaCron, etaQueue
from app.lib.cron.renamer import startRenamerCron
from app.lib.cron.trailer import startTrailerCron, trailerQueue
from app.lib.cron.yarr import startYarrCron
from app.lib.provider.movie.search import movieSearcher
from app.lib.provider.yarr.search import Searcher
from app.lib.sabNzbd import sabNzbd
from cherrypy.process import plugins
import cherrypy
import sys

log = CPLog(__name__)

class CronJobs(plugins.SimplePlugin):

    config = {}
    threads = {}
    searchers = {}

    def __init__(self, bus, config, debug):
        plugins.SimplePlugin.__init__(self, bus)

        self.config = config
        self.debug = debug

    def start(self):

        config = self.config

        log.info("Starting Cronjobs.")
        self.config = config

        #searchers
        yarrSearch = Searcher(config, self.debug);
        movieSearch = movieSearcher(config);
        self.searchers['yarr'] = yarrSearch
        self.searchers['movie'] = movieSearch

        #trailer cron
        trailerCronJob = startTrailerCron(config, self.debug)
        self.threads['trailer'] = trailerCronJob
        self.searchers['trailerQueue'] = trailerQueue

        etaCron = startEtaCron(self.debug)
        self.threads['eta'] = etaCron
        self.searchers['etaQueue'] = etaQueue

        #renamer cron
        renamerCronJob = startRenamerCron(config, self.searchers, self.debug)
        self.threads['renamer'] = renamerCronJob

        #nzb cronjob
        yarrCronJob = startYarrCron(config, self.debug, yarrSearch)
        yarrCronJob.sabNzbd = sabNzbd(config)
        self.threads['yarr'] = yarrCronJob

        #log all errors/tracebacks to logfile
        #sys.stderr = LogFile('stderr')

    def stop(self):
        log.info("Stopping Cronjobs.")
        for t in self.threads.itervalues():
            if t.quit:
                t.quit()
            t.join()

    start.priority = 70
