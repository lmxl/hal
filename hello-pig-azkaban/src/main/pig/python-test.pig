sh echo `pwd` > tmp.txt
fs -rm -r -f $output_path
fs -mkdir -p $output_path
fs -copyFromLocal tmp.txt $output_path