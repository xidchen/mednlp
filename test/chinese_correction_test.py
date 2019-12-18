from __future__ import print_function
import argparse
from ailib.client.ai_service_client import AIServiceClient
import time
import sys

ccc = AIServiceClient(cfg_path='../etc/cdss.cfg', service='AIService', port=2040)


def compute_metric_from_file(in_filename, ref_filename=None):
    if sys.version >= '3':
        f_in = open(in_filename, 'r', encoding='utf-8')
    else:
        f_in = open(in_filename, 'r')
    num_lines = 0
    diff_lines = 0
    start_time = time.time()
    if ref_filename is None:
        for line in f_in:
            line = line.strip()
            line = ''.join(line.split(' '))
            if sys.version >= '3':
                response = ccc.query({'q': line, 'source': str(789)}, service='chinese_correct', method='get')
            else:
                response = ccc.query({'q': line.decode('utf-8'), 'source': str(789)}, service='chinese_correct',
                                     method='get')
            data = response.get('data')
            output_text = data.get('correct')
            if line != output_text:
                diff_lines += 1
            num_lines += 1
        print('model precision rate: {} %, time elapsed {:.1f}s, average inference time {:.3f}s'.format(
            float(num_lines - diff_lines) * 100 / num_lines,
            time.time() - start_time, (time.time() - start_time) / num_lines))
    else:
        if sys.version >= '3':
            f_ref = open(in_filename, 'r', encoding='utf-8')
        else:
            f_ref = open(in_filename, 'r')
        for in_line, ref_line in zip(f_in, f_ref):
            in_line = in_line.strip()
            ref_line = ref_line.strip()
            in_line = ''.join(in_line.split(' '))
            ref_line = ''.join(ref_line.split(' '))
            if sys.version >= '3':
                response = ccc.query({'q': in_line, 'source': str(789)}, service='chinese_correct', method='get')
            else:
                response = ccc.query({'q': in_line.decode('utf-8'), 'source': str(789)}, service='chinese_correct', method='get')
                ref_line = ref_line.decode('utf-8')
            data = response.get('data')
            output_text = data.get('correct')
            if ref_line != output_text:
                diff_lines += 1
            num_lines += 1
        print('model recall rate: {} %, time elapsed {:.1f}s, average inference time {:.3f}s'.format(
            float(num_lines - diff_lines) * 100 / num_lines,
            time.time() - start_time, (time.time() - start_time) / num_lines))
        f_ref.close()
    f_in.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--in_filename", type=str, default=None, help='input test file directory')
    parser.add_argument("--ref_filename", type=str, default=None, help='reference test file directory')
    args = parser.parse_args()
    in_filename = args.in_filename
    ref_filename = args.ref_filename
    if in_filename is not None:
        if ref_filename is not None:
            compute_metric_from_file(in_filename, ref_filename)
        else:
            compute_metric_from_file(in_filename)
    else:
        raise ValueError('please input a test file')