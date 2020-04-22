import matplotlib.pyplot as plt

def build_donut_plot(self,data,label):
  group_names=[]
  group_size=[]
  subgroup_names=[]
  subgroup_size=[]
  for key in data:
    label_key = label+"_level"+key.split("_C")[-1]
    if (not label_key in group_names):
      group_names.append(label_key)
      group_size.append(len(list(set(data[key]))))
    i=0
    for v in data[key]:
      if (not data[key][i] in subgroup_names):
        subgroup_names.append(data[key][i])
        subgroup_size.append(1)
      i+=1

  fig, ax = plt.subplots(figsize=(10,10))
  ax.axis('equal')
  mypie, _ = ax.pie(group_size, radius=1.3, labels=group_names )
  plt.setp( mypie, width=0.3, edgecolor='white')

  # Second Ring (Inside)
  mypie2, _ = ax.pie(subgroup_size, radius=1.3-0.3, labels=subgroup_names, labeldistance=0.7)
  plt.setp( mypie2, width=0.4, edgecolor='white')
  plt.margins(0,0)
  return plt

def make_clickable(self,label,url):
    return '<a href="{}" target="_blank">{}</a>'.format(url,label)
