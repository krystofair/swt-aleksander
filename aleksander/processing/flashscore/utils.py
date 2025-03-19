import logging
import pathlib
import os
import re
import copy

import orjson as jsonlib
import multidict
from slugify import slugify

from aleksander import exc
from aleksander.utils import converters

log = logging.getLogger(__name__)


def cut_json_from_html_fragment(body):
    templ_filename = "match-event.json"
    path = pathlib.Path(os.path.dirname(__file__)).joinpath(pathlib.Path(templ_filename))
    if 'window.environment' not in body:
        raise exc.BuildModelException(portal='flashscore', field='window.environment', prototype='Lack of variable from javascript script in html data.')
    var_idx = body.index('window.environment')
    try:
        rel_start_idx = body[var_idx:].index('{')
        rel_end_idx = body[var_idx:].index('};')
        json_payload = body[var_idx + rel_start_idx : var_idx + rel_end_idx + 1]
        log.debug(json_payload[:30])
        return jsonlib.loads(json_payload)
    except ValueError as e:
        if 'substring not found' in e:
            raise exc.BuildModelException(portal='flashscore', field='window.environment', prototype='Lack of variable from javascript script in html data.')
        log.exception(e)
    except jsonlib.JSONDecodeError as e:
        log.error(e)
    return None


def raw(data):
    """
        Example groups:
        {SD:434, SG:Interceptions, SH:2, SI:4},
        {SE:Extra Time}
    """
    log.debug(data)
    groups = data.split('~')
    log.debug(groups[-5:])
    for group in groups:
        md = multidict.MultiDict()
        # In parts keys are doubled
        parts = group.split('¬')
        log.debug(parts[-5:])
        for part in parts:
            log.debug(part)
            if not part:
                continue
            key, value = part.split('÷')
            md.extend({key: value})
        #: yielding groups
        yield md


def try_split_stat_with_effectivity_form(stat):
        """
            Split statistic for two version. This is for 30% (x/89)
            So effectivity is 30%, but total value is 89 in this example.
            Returns tuple of divided stat or old stat as in list
            for stable interface.
        """
        
        def effs_conv(x):
            if '%' in x:
                return float(x.rstrip('%')) / 100
            else:
                return float(x)
        #: Look that first group is taken with `%` (percent sign).
        EFFECTIVE_PATTERN = r"(\d+%)[ ]\(\d+/(\d+)\)"  # 2 groups: percent, total
        #: add suffix for name of stat type 'percent'.
        if not re.search(EFFECTIVE_PATTERN, stat.get('home', "?")):
            return [stat]
        try:
            #: Prepare new stats from first - copy for safety
            two_stats = {'percent': copy.deepcopy(stat), 'total': copy.deepcopy(stat)}
            two_stats['percent']['name'] = "{}-eff".format(stat['name'])
            for i, kind in enumerate(two_stats):
                home = re.search(EFFECTIVE_PATTERN, stat.get('home', "?"))
                away = re.search(EFFECTIVE_PATTERN, stat.get('away', "?"))
                if home and away:
                    #: i is depend of kind so i+1 will get group(1) for kind 'percent' and so on.
                    two_stats[kind]['home'] = effs_conv(home.group(i + 1))
                    two_stats[kind]['away'] = effs_conv(away.group(i + 1))
            # All goes well returns values
            return list(two_stats.values())
        except:
            return [stat]


def to_float(x):
    if isinstance(x, (float, int)):
        return float(x)
    if isinstance(x, str):
        if '%' in x:
            return float(x.rstrip('%')) / 100
        elif '/' in x:
            a, b = x.split('/', 1)
            return float(a) / float(b)
        else:
            return float(x)
    raise TypeError(x)

def cut_round_in_league_converter(league):
    """Slugify league and cut off a "-round-[0-9]+" suffix."""
    l = slugify(league)
    if "-round" in l:
        start_round_index = l.index("-round") + 1
        return l[:start_round_index]
    return l
