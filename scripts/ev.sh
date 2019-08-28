for i in data/ERCOT*.xls; 
do 
	bn=$(basename $i)
	name=${bn%.*}
	echo $name $i
	python3 scripts/ev.py --input "$i" --name "$name"
done
