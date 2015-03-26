import sys
import os
import datetime
import bluenote
from bluenote.search import Search
from bluenote.search.query import Query
import bluenote.filter
import bluenote.alert

BN_HOME = os.environ.get('BN_HOME')
logger = bluenote.get_logger('blutenote.workers')

s = Search()
def bnd(es, alert):
    should_alert = False
    if alert.get('disabled') == 1: 
        return

    nag_threshold = bluenote.relative_time_to_seconds( bluenote._get(alert, 0, 'alert', 'threshold') )

    logger.info('last alert for %s was %s' % ( alert['name'], bluenote.epoch2iso(bluenote.alert.last_run(es, alert['name']))))
    if bluenote.alert.last_run(es, alert['name']) > 0:
        time_since = ( bluenote.get_current_time_local() - bluenote.alert.last_run(es, alert['name']))
        if time_since <= nag_threshold: 
            # No need to go any further, we havent hit our threshold yet
            return

    try:
        res = s.query(alert['query'], exclude=alert.get('exclude', None),  _from=alert.get('earliest_time', '-1m'), _to=alert.get('latest_time', 'now'))
    except Exception, e:
        logger.exception("Unable to query from worker - alert: %s,  reason: %s" % (alert['name'], e))
        return

    if not res: return

    ## For aggregated results
    if res['intentions']['qd'].has_key('agg_type'):
        intentions = res.get('intentions', None)
        agg_intention = bluenote._get(intentions, None, 'qd', 'agg_type')

        if agg_intention:
            threshold = "%s %s" % ( alert['alert']['relation'], alert['alert']['qty'] )
            
            if 'date_histogram' in agg_intention:
                results = bluenote.filter.date_histogram(res)
                alert_results = bluenote.filter.meets_threshold(results, threshold)
                if len(alert_results['_results']) >= 1:
                    should_alert = True

    else:
    ## For just a standard result set
        alert_results = bluenote.filter.result_set(res)
    
        alert_len = len(alert_results['_results'])
        opr = bluenote.filter.get_operator(alert['alert']['relation'])
        qty = alert['alert']['qty']
        
        if opr(alert_len, qty):
            should_alert = True

    if should_alert:
            # update the alert_triggers
            es.index(index='bluenote-int', doc_type='alert_trigger', id=alert['name'], body={'alert-name': alert['name'], '@timestamp': datetime.datetime.utcnow(), 'time': bluenote.get_current_utc(), 'results': alert_results})
            # log the alert in bluenote-int
            es.index(index='bluenote-int', doc_type='alert-fired', id=bluenote.md5hash("{0}{1}".format(alert['name'], bluenote.get_current_utc())), body={'alert-name': alert['name'], '@timestamp': datetime.datetime.utcnow(), 'time_unix': bluenote.get_current_utc(), 'alert-results': alert_results})

            email_subject = 'Bluenote Alert: {0}'.format(alert['name'])
            email_it = bluenote.alert.email( alert['alert']['action']['email_to'], alert_results, alert['name'], subject=email_subject ) 
            email_it = True
            if email_it:
                logger.info("""msg="{0}", email_to="{1}", name="{2}", subject="{3}" """.format( "Email Sent", alert['alert']['action']['email_to'], alert['name'], email_subject ))

                SCRIPT_DIRS = bluenote.get_bindirs(BN_HOME)

                if alert['alert']['action'].has_key('script'):
                    print bluenote.run_script(alert['alert']['action']['script']['filename'], alert_results)
                #elif alert['alert']['action'].has_key('pymod'):
                #    print bluenote.run_

    return True
