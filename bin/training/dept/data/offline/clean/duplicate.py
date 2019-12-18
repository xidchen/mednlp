class QuerySetter(object):
    def __init__(self):
        self.dict_collection = [dict() for _ in range(20)]

    def find_dict(self, query):
        index = len(query) // 5
        index = min(index, 19)
        duplicate_dict = self.dict_collection[index]

        return duplicate_dict

    def need_to_reserve(self, query):
        reserve = False
        duplicate_dict = self.find_dict(query)

        if query in duplicate_dict:
            duplicate_dict[query] += 1
            # print(query)
        else:
            duplicate_dict[query] = 0
            reserve = True
        return reserve

    def display(self):
        total = 0
        for i, duplicate_dict in enumerate(self.dict_collection):
            duplicated_nums = list(duplicate_dict.values())
            single_total = sum(duplicated_nums)
            print('the {}th dict has {} duplicates'.format(i, single_total))
            total += single_total
        return total
