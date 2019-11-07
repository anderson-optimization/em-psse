for i in ev/ERCOT*.raw; 
do 
	bn=$(basename $i)
	name=${bn%.*}
	echo "Parse Raw ${name} $i"
	echo "python3 lib/em-psse/network.py --input \"$i\" --name \"${name}\" --export"
	python3 lib/em-psse/network.py --input "$i" --name "$name" --export
done
