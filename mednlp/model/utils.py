#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
utils.py
"""


def normal_probability(disease_pop):
    """
    概率归一化.
    """
    total_pop = 0.0
    for pop in disease_pop.values():
        total_pop += pop
    for disease, pop in disease_pop.items():
        if total_pop < 0.000000000001:
            continue
        disease_pop[disease] /= total_pop
    return disease_pop


def sort(disease_pop):
    pop_list = sorted(disease_pop.items(), key=lambda d: (d[1], d[0]),
                      reverse=True)
    disease_list = []
    for disease, pop in pop_list:
        disease_list.append({'disease_id': disease, 'score': pop})
    return disease_list


def f7(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def age_segment(age):
    age = int(age)
    seg = [0, 1, 15, 30, 45, 60, 500]
    for i, x in enumerate(seg):
        if 0 < age <= x:
            age = i
            break
    age = str(age)
    return age
