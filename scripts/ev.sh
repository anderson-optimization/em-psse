for i in ev/ERCOT*.xls; 
do 
	bn=$(basename $i)
	name=${bn%.*}
	echo $name $i
	python3 lib/em-psse/scripts/ev.py  -n "${name}" --input "${i}"
done
