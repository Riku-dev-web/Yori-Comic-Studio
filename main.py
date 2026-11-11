import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, simpledialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import json, os, copy, math

W,H=800,1100
BG='#111827'; PANEL='#1f2937'; ACC='#8b5cf6'; WHITE='#f9fafb'
class ComicStudio:
 def __init__(self,root):
  self.root=root;root.title('Yori Comic Studio');root.geometry('1250x850');root.configure(bg=BG)
  self.pages=[[]];self.page=0;self.tool='select';self.color='#111111';self.start=None;self.preview=None;self.selected=None;self.photo_refs=[];self.image_cache={};self.file=None
  self.build();self.redraw()
 def btn(self,parent,label,fn):
  b=tk.Button(parent,text=label,command=fn,bg=PANEL,fg=WHITE,activebackground=ACC,activeforeground='white',relief='flat',padx=11,pady=9,cursor='hand2');b.pack(fill='x',pady=3);return b
 def build(self):
  header=tk.Frame(self.root,bg='#0b1220',height=60);header.pack(fill='x')
  tk.Label(header,text='✦  YORI COMIC STUDIO',font=('Segoe UI',19,'bold'),bg='#0b1220',fg='#c4b5fd').pack(side='left',padx=20,pady=12)
  for name,fn in [('Nouveau',self.new),('Ouvrir',self.open),('Enregistrer',self.save),('Exporter PNG',self.export_png),('Exporter PDF',self.export_pdf)]:
   tk.Button(header,text=name,command=fn,bg='#374151',fg='white',relief='flat',padx=12,pady=9).pack(side='left',padx=4)
  body=tk.Frame(self.root,bg=BG);body.pack(fill='both',expand=True)
  left=tk.Frame(body,bg=BG,width=180);left.pack(side='left',fill='y',padx=12,pady=12);left.pack_propagate(False)
  tk.Label(left,text='OUTILS',bg=BG,fg='#a5b4fc',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(0,10))
  for label,tool in [('↖ Sélection','select'),('✎ Crayon','pen'),('▭ Case / rectangle','rect'),('◯ Ellipse','ellipse'),('▢ Bulle de dialogue','bubble'),('T Texte','text'),('▧ Image','image')]:self.btn(left,label,lambda t=tool:self.set_tool(t))
  self.btn(left,'🎨 Couleur',self.choose_color);self.btn(left,'🗑 Supprimer objet',self.delete_selected)
  tk.Label(left,text='PAGES',bg=BG,fg='#a5b4fc',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(22,8))
  self.page_label=tk.Label(left,bg=BG,fg=WHITE);self.page_label.pack()
  for name,fn in [('◀ Précédente',self.prev_page),('▶ Suivante',self.next_page),('+ Ajouter une page',self.add_page),('− Supprimer la page',self.delete_page)]:self.btn(left,name,fn)
  center=tk.Frame(body,bg='#374151');center.pack(side='left',fill='both',expand=True,padx=5,pady=12)
  self.canvas=tk.Canvas(center,width=W,height=H,bg='white',highlightthickness=0,cursor='crosshair');self.canvas.pack(expand=True,pady=15)
  self.canvas.bind('<ButtonPress-1>',self.down);self.canvas.bind('<B1-Motion>',self.drag);self.canvas.bind('<ButtonRelease-1>',self.up)
  self.canvas.bind('<Double-Button-1>',self.edit_selected)
  right=tk.Frame(body,bg=BG,width=200);right.pack(side='right',fill='y',padx=12,pady=12);right.pack_propagate(False)
  tk.Label(right,text='PROPRIÉTÉS',bg=BG,fg='#a5b4fc',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(0,12))
  tk.Label(right,text='Taille du trait',bg=BG,fg=WHITE).pack(anchor='w');self.stroke=tk.IntVar(value=4)
  tk.Scale(right,from_=1,to=20,variable=self.stroke,orient='horizontal',bg=BG,fg=WHITE,highlightthickness=0).pack(fill='x')
  tk.Label(right,text='Taille du texte',bg=BG,fg=WHITE).pack(anchor='w',pady=(18,0));self.font_size=tk.IntVar(value=32)
  tk.Scale(right,from_=12,to=72,variable=self.font_size,orient='horizontal',bg=BG,fg=WHITE,highlightthickness=0).pack(fill='x')
  tk.Label(right,text='Astuce : double-clique sur un texte\nou une bulle pour le modifier.\n\nSélectionne et déplace les objets\navec la souris.',justify='left',wraplength=190,bg=BG,fg='#9ca3af').pack(anchor='w',pady=30)
  self.status=tk.Label(self.root,text='Prêt • Choisis un outil pour commencer',anchor='w',bg='#0b1220',fg='#cbd5e1',padx=18,pady=8);self.status.pack(fill='x')
 def set_tool(self,t):self.tool=t;self.status.config(text='Outil : '+t)
 def choose_color(self):
  c=colorchooser.askcolor(color=self.color)[1]
  if c:self.color=c
 def items(self):return self.pages[self.page]
 def redraw(self):
  self.canvas.delete('all');self.photo_refs=[]
  for i,o in enumerate(self.items()):
   t=o['type'];x1,y1,x2,y2=o.get('coords',[0,0,0,0]);color=o.get('color','#111111');width=o.get('width',3)
   if t=='rect':self.canvas.create_rectangle(x1,y1,x2,y2,outline=color,width=width,tags=('obj',str(i)))
   elif t=='ellipse':self.canvas.create_oval(x1,y1,x2,y2,outline=color,width=width,tags=('obj',str(i)))
   elif t=='pen':
    pts=o['points'];
    if len(pts)>=4:self.canvas.create_line(*pts,fill=color,width=width,smooth=True,capstyle='round',tags=('obj',str(i)))
   elif t=='text':self.canvas.create_text(x1,y1,text=o.get('text','Texte'),fill=color,font=('Arial',o.get('size',32),'bold'),anchor='nw',width=max(80,x2-x1),tags=('obj',str(i)))
   elif t=='bubble':
    self.canvas.create_oval(x1,y1,x2,y2,fill='white',outline=color,width=width,tags=('obj',str(i)))
    self.canvas.create_polygon(x1+(x2-x1)*.35,y2-7,x1+(x2-x1)*.27,y2+28,x1+(x2-x1)*.55,y2-7,fill='white',outline=color,tags=('obj',str(i)))
    self.canvas.create_text((x1+x2)/2,(y1+y2)/2,text=o.get('text','Dialogue'),fill=color,font=('Arial',o.get('size',24),'bold'),width=max(50,x2-x1-28),justify='center',tags=('obj',str(i)))
   elif t=='image':
    try:
     im=Image.open(o['path']).convert('RGBA');im.thumbnail((max(1,abs(x2-x1)),max(1,abs(y2-y1))))
     ph=ImageTk.PhotoImage(im);self.photo_refs.append(ph);self.canvas.create_image(x1,y1,image=ph,anchor='nw',tags=('obj',str(i)))
    except Exception:self.canvas.create_text(x1,y1,text='Image introuvable',anchor='nw',fill='red')
   if i==self.selected:
    self.canvas.create_rectangle(x1-4,y1-4,x2+4,y2+4,outline=ACC,dash=(5,3),width=2)
  self.page_label.config(text=f'Page {self.page+1} / {len(self.pages)}')
 def hit(self,x,y):
  hits=self.canvas.find_overlapping(x-2,y-2,x+2,y+2)
  for hit in reversed(hits):
   tags=self.canvas.gettags(hit)
   if 'obj' in tags:return int(tags[tags.index('obj')+1])
  return None
 def down(self,e):
  self.start=(e.x,e.y);self.selected=None
  if self.tool=='select':self.selected=self.hit(e.x,e.y);self.redraw();return
  if self.tool=='text':
   text=simpledialog.askstring('Ajouter un texte','Ton texte :',parent=self.root)
   if text:self.items().append(dict(type='text',coords=[e.x,e.y,min(W,e.x+350),e.y+120],text=text,color=self.color,size=self.font_size.get()));self.redraw()
  elif self.tool=='image':
   path=filedialog.askopenfilename(filetypes=[('Images','*.png *.jpg *.jpeg *.webp *.bmp')])
   if path:
    with Image.open(path) as im:w,h=im.size
    scale=min(350/w,350/h,1);self.items().append(dict(type='image',path=path,coords=[e.x,e.y,e.x+int(w*scale),e.y+int(h*scale)]));self.redraw()
  elif self.tool=='pen':self.items().append(dict(type='pen',points=[e.x,e.y],coords=[e.x,e.y,e.x,e.y],color=self.color,width=self.stroke.get()))
 def drag(self,e):
  if not self.start:return
  sx,sy=self.start
  if self.tool=='select' and self.selected is not None:
   o=self.items()[self.selected];dx=e.x-sx;dy=e.y-sy;o['coords']=[o['coords'][0]+dx,o['coords'][1]+dy,o['coords'][2]+dx,o['coords'][3]+dy]
   if o['type']=='pen':o['points']=[v+(dx if i%2==0 else dy) for i,v in enumerate(o['points'])]
   self.start=(e.x,e.y);self.redraw()
  elif self.tool=='pen':
   o=self.items()[-1];o['points'] += [e.x,e.y];xs=o['points'][::2];ys=o['points'][1::2];o['coords']=[min(xs),min(ys),max(xs),max(ys)];self.redraw()
  elif self.tool in ('rect','ellipse','bubble'):
   self.redraw();a,b,c,d=min(sx,e.x),min(sy,e.y),max(sx,e.x),max(sy,e.y)
   if self.tool=='rect':self.canvas.create_rectangle(a,b,c,d,outline=ACC,width=2,dash=(4,4))
   else:self.canvas.create_oval(a,b,c,d,outline=ACC,width=2,dash=(4,4))
 def up(self,e):
  if not self.start:return
  if self.tool in ('rect','ellipse','bubble'):
   sx,sy=self.start;a,b,c,d=min(sx,e.x),min(sy,e.y),max(sx,e.x),max(sy,e.y)
   if c-a>8 and d-b>8:
    o=dict(type=self.tool,coords=[a,b,c,d],color=self.color,width=self.stroke.get(),size=self.font_size.get())
    if self.tool=='bubble':o['text']=simpledialog.askstring('Bulle','Dialogue :',parent=self.root) or 'Dialogue'
    self.items().append(o)
  self.start=None;self.redraw()
 def edit_selected(self,e):
  i=self.hit(e.x,e.y)
  if i is not None and self.items()[i]['type'] in ('text','bubble'):
   o=self.items()[i];s=simpledialog.askstring('Modifier le texte','Texte :',initialvalue=o['text'],parent=self.root)
   if s is not None:o['text']=s;self.redraw()
 def delete_selected(self):
  if self.selected is not None:self.items().pop(self.selected);self.selected=None;self.redraw()
 def add_page(self):self.pages.append([]);self.page=len(self.pages)-1;self.selected=None;self.redraw()
 def prev_page(self):self.page=max(0,self.page-1);self.selected=None;self.redraw()
 def next_page(self):self.page=min(len(self.pages)-1,self.page+1);self.selected=None;self.redraw()
 def delete_page(self):
  if len(self.pages)>1:self.pages.pop(self.page);self.page=min(self.page,len(self.pages)-1)
  else:self.pages=[[]];self.page=0
  self.selected=None;self.redraw()
 def new(self):
  if messagebox.askyesno('Nouveau projet','Effacer le projet actuel ?'):
   self.pages=[[]];self.page=0;self.file=None;self.selected=None;self.redraw()
 def save(self):
  path=self.file or filedialog.asksaveasfilename(defaultextension='.ycomic',filetypes=[('Projet Yori Comic','*.ycomic')])
  if not path:return
  try:
   with open(path,'w',encoding='utf-8') as f:json.dump({'version':1,'pages':self.pages},f,ensure_ascii=False,indent=2)
   self.file=path;self.status.config(text='Enregistré : '+path)
  except Exception as e:messagebox.showerror('Erreur',str(e))
 def open(self):
  path=filedialog.askopenfilename(filetypes=[('Projet Yori Comic','*.ycomic')]);
  if not path:return
  try:
   with open(path,encoding='utf-8') as f:data=json.load(f)
   self.pages=data['pages'];self.page=0;self.file=path;self.selected=None;self.redraw()
  except Exception as e:messagebox.showerror('Erreur',str(e))
 def font(self,size):
  for p in ['C:/Windows/Fonts/arialbd.ttf','C:/Windows/Fonts/arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
   if os.path.exists(p):return ImageFont.truetype(p,max(8,int(size)))
  return ImageFont.load_default()
 def render(self,items):
  im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im)
  for o in items:
   t=o['type'];x1,y1,x2,y2=[int(v) for v in o.get('coords',[0]*4)];color=o.get('color','#111111');w=o.get('width',3)
   if t=='rect':d.rectangle((x1,y1,x2,y2),outline=color,width=w)
   elif t=='ellipse':d.ellipse((x1,y1,x2,y2),outline=color,width=w)
   elif t=='pen' and len(o['points'])>=4:d.line(o['points'],fill=color,width=w,joint='curve')
   elif t=='text':d.multiline_text((x1,y1),o['text'],font=self.font(o.get('size',32)),fill=color,spacing=5)
   elif t=='bubble':
    d.ellipse((x1,y1,x2,y2),fill='white',outline=color,width=w)
    d.polygon([(x1+(x2-x1)*.35,y2-5),(x1+(x2-x1)*.27,y2+28),(x1+(x2-x1)*.55,y2-5)],fill='white')
    text=o.get('text','Dialogue');font=self.font(o.get('size',24));box=d.multiline_textbbox((0,0),text,font=font);tw=box[2]-box[0];th=box[3]-box[1];d.multiline_text(((x1+x2-tw)/2,(y1+y2-th)/2),text,font=font,fill=color,align='center')
   elif t=='image':
    try:
     with Image.open(o['path']) as src:
      src=src.convert('RGB');src.thumbnail((max(1,x2-x1),max(1,y2-y1)));im.paste(src,(x1,y1))
    except Exception:pass
  return im
 def export_png(self):
  path=filedialog.asksaveasfilename(defaultextension='.png',filetypes=[('PNG','*.png')]);
  if path:self.render(self.items()).save(path);messagebox.showinfo('Export','Page exportée en PNG !')
 def export_pdf(self):
  path=filedialog.asksaveasfilename(defaultextension='.pdf',filetypes=[('PDF','*.pdf')]);
  if path:
   try:
    ims=[self.render(p) for p in self.pages];ims[0].save(path,'PDF',save_all=True,append_images=ims[1:],resolution=100);messagebox.showinfo('Export','BD exportée en PDF !')
   except Exception as e:messagebox.showerror('Erreur',str(e))
if __name__=='__main__':
 root=tk.Tk();ComicStudio(root);root.mainloop()
