from pprint import pprint 
import bluenote
import bluenote.filter
import pandas as pd
import sys

def _set(results):
    return results

    intentions = results['intentions']
    rset = []
    
    if intentions['qd']['agg_type']:
        rset.append(bluenote.flatten_dict(get_aggs(results)))

    for result in results['_results']['hits']['hits']:
            rdict = {}

            rdict['_index'] = result.get('_index')
            rdict['_score'] = result.get('_score')
            rdict['_type'] = result.get('_type')
            
            for rs in result['fields']['partial']:
                if isinstance(rs, dict):
                    for k,v in rs.iteritems():
                        if isinstance(v, dict):
                            flatd = bluenote.flatten_dict(rs)
                            for k,v in flatd.iteritems():
                                rdict[k] = v
                        else: 
                            rdict[k] = v
            rset.append(rdict)
    return rset


def get_aggs(res):
    
    intentions = res['intentions']
    agg_type = intentions['qd']['agg_type']

    if 'date_histogram' in agg_type:
        retres = bluenote.filter.date_histogram(res)


    results = retres['_results']
    return bluenote.flatten_dict(results)
