# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------
# Copyright (c) 2009  Jendrik Seipp
#
# RedNotebook is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# RedNotebook is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with RedNotebook; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# -----------------------------------------------------------------------

from __future__ import division

import datetime
import logging

TEXT_RESULT_LENGTH = 50


def get_text_with_dots(text, start, end, found_text=None):
    '''
    Find the outermost spaces and add dots if needed
    '''
    bound1 = max(0, start - int(TEXT_RESULT_LENGTH//2))
    bound2 = start
    bound3 = end
    bound4 = min(len(text), end + int(TEXT_RESULT_LENGTH//2))

    if bound1 == 0:
        start = 0
    else:
        start = max(bound1, text.find(' ', bound1, bound2))

    if bound4 == len(text):
        end = len(text)
    else:
        end = text.rfind(' ', bound3, bound4)
        if end == -1:
            end = bound4

    res = ''
    if start > 0:
        res += '... '
    res += text[start:end]
    if end < len(text):
        res += ' ...'

    res = res.replace('\n', ' ')

    if found_text:
        # Make the searched_text bold
        res = res.replace(found_text, 'STARTBOLD%sENDBOLD' % found_text)

    return res


class Day(object):
    def __init__(self, month, day_number, day_content = None):
        if day_content == None:
            day_content = {}

        self.date = datetime.date(month.year_number, month.month_number, day_number)

        self.month = month
        self.day_number = day_number
        self.content = day_content

    # Text
    def _get_text(self):
        '''
        Returns the day's text encoded as UTF-8
        decode means "decode from the standard ascii representation"
        '''
        if 'text' in self.content:
            return self.content['text'].decode('utf-8')
        else:
           return ''

    def _set_text(self, text):
        self.content['text'] = text
    text = property(_get_text, _set_text)

    def _has_text(self):
        return len(self.text.strip()) > 0
    has_text = property(_has_text)


    @property
    def empty(self):
        if len(self.content.keys()) == 0:
            return True
        elif len(self.content.keys()) == 1 and 'text' in self.content and not self.has_text:
            return True
        else:
            return False


    @property
    def tree(self):
        tree = self.content.copy()
        if 'text' in tree:
            del tree['text']
        return tree


    def add_category_entry(self, category, entry):
        if category in self.content:
            self.content[category][entry] = None
        else:
            self.content[category] = {entry: None}


    def merge(self, same_day):
        assert self.date == same_day.date

        # Merge texts
        text1 = self.text.strip()
        text2 = same_day.text.strip()
        if text2 in text1:
            # self.text contains the other text
            pass
        elif text1 in text2:
            # The other text contains contains self.text
            self.text = same_day.text
        else:
            self.text += '\n\n' + same_day.text

        # Merge categories
        for category, entries in same_day.get_category_content_pairs().items():
            for entry in entries:
                self.add_category_entry(category, entry)


    @property
    def categories(self):
        return self.tree.keys()


    @property
    def tags(self):
        return self.get_entries('Tags')


    def get_entries(self, category):
        return sorted(self.get_category_content_pairs().get(category, []))


    def get_category_content_pairs(self):
        '''
        Returns a dict of (category: content_in_category_as_list) pairs.
        content_in_category_as_list can be empty
        '''
        original_tree = self.tree.copy()
        pairs = {}
        for category, content in original_tree.iteritems():
            entry_list = []
            if content is not None:
                for entry, nonetype in content.iteritems():
                    entry_list.append(entry)
            pairs[category] = entry_list
        return pairs


    def get_words(self, with_special_chars=False):
        if with_special_chars:
            return self.text.split()

        word_list = self.text.split()
        real_words = []
        for word in word_list:
            word = word.strip(u'.|-!"/()=?*+~#_:;,<>^°´`{}[]\\')
            if len(word) > 0:
                real_words.append(word)
        return real_words


    def get_number_of_words(self):
        return len(self.get_words(with_special_chars=True))


    def get_date_and_start_of_text(self):
        return (str(self), get_text_with_dots(self.text, 0, TEXT_RESULT_LENGTH))


    def search_text(self, search_text):
        '''
        Try searching in date first, then in the text, then in the annotations
        Uses case-insensitive search
        '''
        # Search in date
        date = str(self)
        if search_text in date:
            return self.get_date_and_start_of_text()

        # Search in text
        upcase_search_text = search_text.upper()
        upcase_day_text = self.text.upper()
        occurence = upcase_day_text.find(upcase_search_text)

        # Check if search_text is in text
        if occurence > -1:
            found_text = self.text[occurence:occurence + len(search_text)]

            result_text = get_text_with_dots(self.text, occurence,
                                    occurence + len(search_text), found_text)
            return (date, result_text)

        # Check if search_text is in annotations
        for category, content_list in self.get_category_content_pairs().items():
            if search_text.upper() in category.upper():
                return self.get_date_and_start_of_text()

            for tag in content_list:
                if search_text.upper() in tag.upper():
                    return self.get_date_and_start_of_text()


    def search_category(self, search_category):
        results = []
        for category, content in self.get_category_content_pairs().items():
            if content:
                if search_category.upper() in category.upper():
                    for entry in content:
                        results.append((str(self), entry))
        return results


    def search_tag(self, search_tag):
        for category, content_list in self.get_category_content_pairs().items():
            if not category.upper() == 'TAGS' or not content_list:
                continue
            if not search_tag.upper() in [tag.upper() for tag in content_list]:
                continue

            return self.get_date_and_start_of_text()


    def __str__(self):
        return self.date.strftime('%Y-%m-%d')


    def __cmp__(self, other):
        return cmp(self.date, other.date)



class Month(object):
    def __init__(self, year_number, month_number, month_content = None):
        if month_content == None:
            month_content = {}

        self.year_number = year_number
        self.month_number = month_number
        self.days = {}
        for day_number, day_content in month_content.iteritems():
            self.days[day_number] = Day(self, day_number, day_content)

        self.edited = False

    def get_day(self, day_number):
        if day_number in self.days:
            return self.days[day_number]
        else:
            new_day = Day(self, day_number)
            self.days[day_number] = new_day
            return new_day

    def set_day(self, day_number, day):
        self.days[day_number] = day

    def __str__(self):
        res = 'Month %s %s\n' % (self.year_number, self.month_number)
        for day_number, day in self.days.iteritems():
            res += '%s: %s\n' % (day_number, day.text)
        return res

    @property
    def empty(self):
        for day in self.days.values():
            if not day.empty:
                return False
        return True

    def same_month(date1, date2):
        if date1 == None or date2 == None:
            return False
        return date1.month == date2.month and date1.year == date2.year
    same_month = staticmethod(same_month)

    def __cmp__(self, other):
        return cmp((self.year_number, self.month_number),
                    (other.year_number, other.month_number))
