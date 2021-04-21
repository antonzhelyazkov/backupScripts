def nvidia_smi_parse(info):
    data = {}
    for i, line in enumerate(info):
        if len(line) != 4:
            continue # Skip unexpected lines
        pool_name, pm_type, metric, value = line
        item = '%s [%s]' % (pool_name, pm_type)
        if item not in data:
            data[item] = {}

        data[item][metric] = int(value)

    return data


def inventory_nvidia_smi(info):
    data = nvidia_smi_parse(info)
    inv = []
    for item in data.keys():
        inv.append((item, {}))
    return inv


def check_nvidia_smi(item, params, info):
    if params is None:
        params = {}

    all_data = nvidia_smi_parse(info)
    if item not in all_data:
        return 3, 'Unable to find instance in agent output'
    data = all_data[item]

    perfkeys = [
        'gpu_utilization', 'memory_used', 'temperature',
        'graphics_clock', 'msm_clock',
    ]
    # Add some more values, derived from the raw ones...
    this_time = int(time.time())
    # for key in ['accepted_conn', 'max_children_reached', 'slow_requests']:
    #    per_sec = get_rate("nginx_status.%s" % key, this_time, data[key])
    #    data['%s_per_sec' % key] = per_sec
    #    perfkeys.append('%s_per_sec' % key)

    perfdata = []
    for i, key in enumerate(perfkeys):
        perfdata.append( (key, data[key]) )
    perfdata.sort()

    worst_state = 0

    proc_warn, proc_crit = params.get('gpu_utilization', (None, None))
    proc_txt = ''
    if proc_crit is not None and data['gpu_utilization'] > proc_crit:
        worst_state = max(worst_state, 2)
        proc_txt = ' (!!)'
    elif proc_warn is not None and data['gpu_utilization'] > proc_warn:
        worst_state = max(worst_state, 1)
        proc_txt = ' (!)'

    output = [
        'Active: %d%s (%d idle, %d waiting)' % (
            data['gpu_utilization'], proc_txt, data['memory_used'], data['temperature'],
        ),
        'Started %s ago' % (get_age_human_readable(data['graphics_clock'])),
        'Requests: %0.2f/s' % (data['msm_clock']),
    ]

    return worst_state, ', '.join(output), perfdata

check_info['php_fpm_pools'] = {
    "check_function" :      check_nvidia_smi,
    "inventory_function" :  inventory_nvidia_smi,
    "service_description" : "PHP-FPM Pool %s Status",
    "has_perfdata" :        True,
    "group" :               "php_fpm_pools"
}
