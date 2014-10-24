import sys
import os
import collections
import ConfigParser
import bluenote

from pprint import pprint 

class Config(object):
    
    def __init__(self, configs):
        self.CONFS = self.flatten(configs)
        self.globalconf = []
        self.config = ConfigParser.ConfigParser()
        self.load_all()


    def load_all(self):
        for conf in self.CONFS:
            filename = os.path.basename(conf)
            if 'inputs' in filename:
                self.parse_inputs(conf)
            if 'outputs' in filename:
                self.parse_outputs(conf)
            if 'alerts' in filename:
                self.parse_alerts(conf)


    def parse_inputs(self, conf):
        self.inputs = [] 
        self.config.read(conf)
        stanzas = []
        for section_name in self.config.sections():
            stanzas.append(section_name)

        for stanza in stanzas:
            itemd = {}
            if "://" in stanza:
                method, location = stanza.split("://")
                itemd = { method: { location: {}}}
                for option in self.config.options(stanza):
                    itemd[method][location][option] = self.config.get(stanza, option)
                self.inputs.append(itemd)


    def parse_outputs(self, conf):
        self.outputs = {} 
        self.config.read(conf)

        itemd = {}
        for option in self.config.options('elasticsearch'):
            stanza = "elasticsearch"
            if 'host' in option:
                if ',' in self.config.get(stanza, option):
                    hosts = self.config.get(stanza, option).split(",")
                    hosts = [x.strip() for x in hosts]
                    itemd['host'] = hosts
                else:
                    itemd['host'] = self.config.get(stanza, option)
        self.outputs.update(itemd)

    def parse_alerts(self, conf):


        self.alerts = []
        self.config.read(conf)

        stanzas = []
        for section_name in self.config.sections():
            stanzas.append(section_name)

        for stanza in stanzas:
            itemd = {}
            itemd[stanza] = {} 
            itemd[stanza]['aggs'] = [] 
            for option in self.config.options(stanza):
                if '.' in option:
                    parts = option.split('.')
                    if 'aggs' in parts[0]:
                        if int(parts[1]):
                            aggsd = {}
                            lst_index = int(parts[1])
                            agg_name = self.config.get(stanza, "%s.%s.%s" % ( parts[0], parts[1], 'name'))
                            agg_terms = ['terms', 'date_histogram', 'histogram', 'avg']
                            if len(parts) > 3:
                                if parts[2] in agg_terms:
                                    agg_type = parts[2]
                                    agg_option = parts[3]

                                    aggsd[agg_name] = []
                                    aggsd[agg_name].append({ agg_option: self.config.get(stanza, option) })

                                    itemd[stanza]['aggs'].append(aggsd)

            self.alerts.append(itemd)

        pprint(self.alerts)

    def flatten(self, l):
        for el in l:
            if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
                for sub in self.flatten(el):
                    yield sub
            else:
                yield el
        
