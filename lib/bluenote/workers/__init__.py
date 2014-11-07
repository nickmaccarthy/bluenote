import sys
import os
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

    if bluenote.alert.last_run(es, alert['name']) > 0:
        time_since = ( bluenote.get_current_time_local() - bluenote.alert.last_run(es, alert['name']))
        if time_since <= nag_threshold: 
            # No need to go any further, we havent hit our threshold yet
            return

    try:
        res = s.query(alert['query'], _from=alert.get('earliest_time', '-1m'), _to=alert.get('latest_time', 'now'))
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
        
        if len(alert_results['_results']) > 0:
            should_alert = True

    if should_alert:
            email_subject = 'Bluenote Alert: %s' % alert['name']
            email_it = bluenote.alert.email( alert['alert']['action']['email_to'], alert_results, alert['name'], subject=email_subject ) 
            email_it = True
            if email_it:
                logger.info("""msg="%s", email_to="%s", name="%s", subject="%s" """ % ( "Email Sent", alert['alert']['action']['email_to'], alert['name'], email_subject ))
                es.index(index='bluenote-int', doc_type='alert_trigger', id=alert['name'], body={'alert-name': alert['name'], 'time': bluenote.get_current_utc(), 'results': alert_results})

                SCRIPT_DIRS = bluenote.get_bindirs(BN_HOME)

                if alert['alert']['action'].has_key('script'):
                    print bluenote.run_script(alert['alert']['action']['script']['filename'], alert_results)
                #elif alert['alert']['action'].has_key('pymod'):
                #    print bluenote.run_

    return True