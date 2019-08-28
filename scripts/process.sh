for i in data/ERCOT*.raw; 
do 
	bn=$(basename $i)
	name=${bn%.*}
	echo $name $i
	python3 network.py --input "$i" --name "$name" --export
done
