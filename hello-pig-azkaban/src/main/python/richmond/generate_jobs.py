import sys, os

work_path = '~/tmp/richmond-fixed'
work_path = os.path.expanduser(work_path)
rp = 10
for i in range(rp):
    for r in range(0,11):
        ratio = 1.0 * r / 10
        file_path = work_path + '/ratio_%.2f_fold_%d' % (ratio, i)
        fp = open(file_path, mode='w')
        fp.write(str(ratio))
        fp.close()



