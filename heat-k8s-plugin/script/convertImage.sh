cat test | while  read line
do
  docker pull $line	
  newtag=$(echo $line | sed s/ali/xa/g)
  docker tag $line $newtag
  docekr push $newtag 
done

 
