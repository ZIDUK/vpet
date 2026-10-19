"""Read-only serial observation; sends no commands and never requests a reset."""
import argparse
import json
import time


def summarize(lines):
    samples=[]
    fatal=[]
    restarts=0
    for line in lines:
        if any(word in line.lower() for word in
               ('guru meditation','backtrace:','brownout','stack canary','vpet_fatal')):
            fatal.append(line)
        if not line.startswith('VPET_RUNTIME '):
            continue
        fields=dict(token.split('=',1) for token in line.split()[1:] if '=' in token)
        try:
            sample={key:int(fields[key]) for key in
                    ('uptime_ms','heap_free','heap_min','loop_max_us','ble')}
        except (ValueError,KeyError):
            continue
        if any(value<0 for value in sample.values()):
            continue
        if samples and 0<samples[-1]['uptime_ms']-sample['uptime_ms']<2**31:
            restarts+=1
        samples.append(sample)
    return {
        'runtime_samples':len(samples),
        'liveness_observed':len(samples)>=2 and not fatal and not restarts and
                            samples[-1]['uptime_ms']!=samples[0]['uptime_ms'],
        'heap_free_min':min((s['heap_free'] for s in samples),default=None),
        'heap_free_max':max((s['heap_free'] for s in samples),default=None),
        'heap_minimum_watermark':min((s['heap_min'] for s in samples),default=None),
        'loop_max_us':max((s['loop_max_us'] for s in samples),default=None),
        'input_events':sum(line.startswith('VPET_INPUT ') for line in lines),
        'ble_states':list(dict.fromkeys(s['ble'] for s in samples)),
        'restarts_observed':restarts,
        'fatal_lines':fatal,
    }


def observe(port, seconds):
    import serial
    lines=[]
    connection=serial.Serial(port=None,baudrate=115200,timeout=.2)
    connection.dtr=False
    connection.rts=False
    connection.port=port
    start=time.monotonic()
    with connection:
        while time.monotonic()-start<seconds:
            line=connection.readline().decode('utf-8',errors='replace').strip()
            if line: lines.append(line)
    report=summarize(lines)
    report.update(duration_seconds=round(time.monotonic()-start,3),port=port,
                  reset_requested=False,commands_sent=0,lines=lines)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',required=True)
    parser.add_argument('--seconds',type=int,default=300)
    args=parser.parse_args()
    if not 20<=args.seconds<=43200:
        parser.error('--seconds must be between 20 and 43200')
    report=observe(args.port,args.seconds)
    print(json.dumps(report,indent=2))
    return 0 if report['liveness_observed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
