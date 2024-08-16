# -*- coding: utf-8 -*-
"""search_engine.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/144YkiyuDW8ZQal77nyWazQDRkU6HXugx

Lookup function works with both [keyword, [url1 ,url2 ...]] index structure and [keyword, [url1 ,url2 ...], count] because it returns the entry.
"""

def lookupListIndex(index, keyword : str):
  for entry in index:
    if entry[0] == keyword:
      return entry
  return None

def union(A, B):
  for element in B:
    if element not in A:
      A.append(element)
  return A

def addToIndex(index : list[str, list[str]], keyword :str, url :str):
  entry = lookupListIndex(index, keyword)
  if entry is None:
    # add new entry
    index.append([keyword, [url]])
  else:
    union(entry[1], [url])

def addToIndexWithCount(index : list[str, list[str], int], keyword :str, url:str):
  entry = lookupListIndex(index, keyword)
  if entry is None:
    # add new entry
    index.append([keyword, [url], 1])
    return
  #update existing entry if url not already there
  if url not in entry[1]:
    entry[1].append(url)
    entry[2] += 1

import urllib.request

def getPage(url):
  try:
    page = urllib.request.urlopen(url).read()
    page = page.decode("utf-8")
    return page
  except:
    return ""

def addPageToIndex(index, url, content):
  contentList=content.split()
  for element in contentList:
    addToIndex(index,element,url)


def getNextTarget(page):
    start_link = page.find('<a href=')
    if start_link == -1:
        return None, 0
    start_quote = page.find('"', start_link)
    end_quote = page.find('"', start_quote + 1)
    url = page[start_quote + 1:end_quote]
    return url, end_quote


def getAllLinks(page):
  urlList=[]
  while True:
    myUrl, lastQuote = getNextTarget(page)
    if myUrl:
      urlList.append(myUrl)
      page=page[lastQuote:]
    else:
      break
  return urlList

def crawlWeb(seed):
  toCrawl=[seed]
  crawled=[]
  index=[]
  while toCrawl:
      page = toCrawl.pop()
      if page not in crawled:
          content = getPage(page)
          addPageToIndex(index, page, content)
          outlinks = getAllLinks(content)
          union(toCrawl, outlinks)
          crawled.append(page)
  return toCrawl, index, crawled

toCrawl , original_index, crawled = crawlWeb("https://searchengineplaces.com.tr/")

print(toCrawl, len(crawled))

for entry in original_index:
  print(entry)

# graphIn: dict[list[str]] = Includes links that directs to the key page
# graphOut: dict[dict[int]] = Includes links that directs out of the key page with how many ooccurences of that outgoing link
# totalOut: dict[int] = Post-webcrawl calculated total links out of the key page
# we need to be able to provide teleportation (damping factor)
# also if a page has no outgoing link it should mean it can go everywhere equally

def calculatePageRank(graphIn, graphOut, totalOut , unifiedPages, noOutgoing ,total_page_count):
  d = 0.85

  N = total_page_count
  rank = {}
  numloops = 1000
  for page in unifiedPages:
    rank[page] = 1 / N

  for i in range(numloops):
    newrank = {}
    for page in unifiedPages:
      newrank[page] = (1 - d) / N
      for node in noOutgoing:
          newrank[page] += d * (rank[node] / N)
      if page in graphIn:
        for node in graphIn[page]:
          newrank[page] += d * (rank[node] / totalOut[node]) * graphOut[node][page]
    rank = newrank
  return rank

def addToGraphIn(graph: dict[list[str]], start, end):
  if end not in graph:
    graph[end] = [start]
  else:
    graph[end].append(start)
  return


def addToGraphOut(graph: dict[dict[int]], start, end):
  if start not in graph:
    graph[start] = {}
    graph[start][end] = 1
  elif end in graph[start]:
    graph[start][end] += 1
  else:
    graph[start][end] = 1
  return

def calculateTotalOut(graph):
  totalOut = {}
  for start in graph:
    for end in graph[start]:
      if start not in totalOut:
        totalOut[start] = graph[start][end]
      else:
        totalOut[start] += graph[start][end]
  return totalOut

def crawlWebWithGraphs(seed):
  toCrawl=[seed]
  crawled=[]
  index=[]
  graphIn : dict[list[str]] = {}
  graphOut : dict[dict[int]] = {}
  noOutgoing : list[str]=  []
  total_crawled = 0
  while toCrawl:
      page = toCrawl.pop()
      if page not in crawled:
          content = getPage(page)
          addPageToIndex(index, page, content)
          outlinks = getAllLinks(content)
          for link in outlinks:
            addToGraphIn(graphIn, page, link)
            addToGraphOut(graphOut, page, link)
          if outlinks == []:
            noOutgoing.append(page)
          union(toCrawl, outlinks)
          crawled.append(page)
          total_crawled += 1
  totalOut = calculateTotalOut(graphOut)
  return index, graphIn, graphOut, totalOut , crawled, noOutgoing, total_crawled

index, graphIn, graphOut, totalOut, unifiedPages, noOutgoing, total_crawled = crawlWebWithGraphs("https://searchengineplaces.com.tr/")

r = calculatePageRank(graphIn, graphOut, totalOut, unifiedPages, noOutgoing, total_crawled)

def total_rank(rank : dict[float]):
  total = 0
  for entry in rank:
    total += rank[entry]
  return total
#this means that total number of surfers remains almost equal to initial start total (1 / n) * n
total = total_rank(r)
print(total)
print(r)

def sort_rank(rank_dict):
  size = 0
  sorted_rank: list[tuple] = []
  for key in rank_dict:
      for i in range(size):
        if rank_dict[key] >= sorted_rank[i][1]:
          sorted_rank = sorted_rank[:i] + [(key, rank_dict[key])] + sorted_rank[i:]
          break
      else:
        sorted_rank.append((key,rank_dict[key]))
      size += 1
  return sorted_rank , size

r_sorted, r_length = sort_rank(r)
for entry in r_sorted:
  print(entry)

def sort_urls_according_to_rank(urls: list[str], total_url_count , rank_list : list[tuple], rank_length : int):
  result = []
  rank_index = 0
  while True:
    for i in range(total_url_count):
      if urls[i] == rank_list[rank_index][0]:
        result.append(urls[i])
    rank_index += 1
    if rank_index == rank_length:
      break
  return result

entry = lookupListIndex(index, "its")

sorted_urls = sort_urls_according_to_rank(entry[1], len(entry[1]), r_sorted, r_length)
for entry in sorted_urls:
  print(entry)

# lets overwrite addPageToIndex
def addPageToIndex(index, url, content):
  contentList=content.split()
  for element in contentList:
    #using previously defined function
    addToIndexWithCount(index,element,url)

toCrawl , index_with_count, crawled = crawlWeb("https://searchengineplaces.com.tr/")

print(toCrawl, len(crawled))

for entry in index_with_count:
  print(entry)

keyword = "its"
entry = lookupListIndex(index_with_count, keyword)
print(f"Keyword:  {keyword}")
if entry is None:
  print("0 result found")
else:
  print(f"{entry[2]} result found")
  print("Urls:")
  for url in entry[1]:
    print(url)

def lookupLink(index, url):
  keywords = []
  count = 0
  for entry in index:
    if url in entry[1] and entry[0] not in keywords:
      keywords.append(entry[0])
      count += 1
  print(f"Link:  {url}")
  print(f"{count} keyword found")
  if count > 0:
    for keyword in keywords:
      print(keyword)
  return keywords, count

keywords, count = lookupLink(index_with_count, "http://www.searchengineplaces.com.tr/oktayrecommends.html")