def find_longest_common(str1, str2):
    m = len(str1)
    n = len(str2)
    # create a 2D-array size m*n
    counter = [[0]*(n+1) for x in range(m+1)]
    longest = 0
    l_set = set()
    for i in range(m):
        for j in range(n):
            if str1[i] == str2[j]:
                c = counter[i][j] + 1
                counter[i+1][j+1] = c
                if c > longest:
                    l_set = set()
                    longest = c
                    l_set.add(str1[i - c + 1:i + 1])
                elif c == longest:
                    l_set.add(str1[i - c + 1:i + 1])
    return l_set


# test 1
# ret = find_longest_common('academy', 'abracadabra')
# for s in ret:
#     print(s)
# test 2

ret = find_longest_common('ababc', 'abcdaba')
for s in ret:
    print(s)

#         a   b   c   d   a   b   a
#     0   0   0   0   0   0   0   0
# a   0   1   0   0   0   1   0   1
# b   0   0   2   0   0   0   2   0
# a   0   1   0   0   0   1   0   3
# b   0   0   2   0   0   0   2   0
# c   0   0   0   3   0   0   0   0
#
# --> find longest common prefix
