
# coding: utf-8

# In[14]:



from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import io
import numpy as np
import boto3
from botocore.errorfactory import ClientError
import operator


# In[2]:


s3 = boto3.client('s3')


# In[3]:


cats = [
    'levicový nevolič',
    'materialista',
    'městský liberál',
    'mladý těkavý',
    'obranář',
    'politicky pasivní',
    'skutečný křesťan'
]

pics = [
    'nevolic.png',
    'materialista.png',
    'liberal.png',
    'tekavy.png',
    'obranar.png',
    'pasivni.png',
    'krestan.png'
]


# In[4]:


template = '<!DOCTYPE html><meta charset="UTF-8">'     + '<meta property="og:url" content="https://dev.datarozhlas.cz/profil-volice/share/{0}.html" />'     + '<meta property="og:type" content="article" />'     + '<meta property="og:title" content="Jsem z {1} % {2}" />'     + '<meta property="og:description" content="Udělejte si také test politické orientace, který připravil server iROZHLAS.cz s Medianem." />'     + '<meta property="og:image" content="https://dev.datarozhlas.cz/profil-volice/share/{0}.png" />'     + '<meta property="og:image:width" content="1204" />'     + '<meta property="og:image:height" content="632" />'     + '<meta name="twitter:card" content="summary_large_image">'     + '<meta name="twitter:site" content="@irozhlascz">'     + '<meta name="twitter:creator" content="@datarozhlas">'     + '<meta name="twitter:title" content="Jsem z {1} % {2}">'     + '<meta name="twitter:description" content="Udělejte si také test politické orientace, který připravil server iROZHLAS.cz s Medianem.">'     + '<meta name="twitter:image" content="https://dev.datarozhlas.cz/profil-volice/share/{0}.png">'     + '<script>window.location.replace("https://www.irozhlas.cz/zpravy-nahled/kalkulacka-median");</script>'


# In[34]:


def make_share(context, env):
    arr = context['arr']
    res = dict(zip(cats, arr))
    res = sorted(res.items(), key=operator.itemgetter(1), reverse=True)
    
    name = '_'.join([str(x) for x in arr])
    
    try:
        s3.head_object(Bucket='datarozhlas', Key='/profil-volice/share/' + name + '.png')
        return name
    except ClientError:   
        # pokud neexistue, vyrobit
        pattern = Image.open('./imgs/canvas.jpg', 'r').convert('RGBA')
        size = width, height = pattern.size
        draw = ImageDraw.Draw(pattern,'RGBA')
        font = ImageFont.truetype('Roboto-Regular.ttf', 58)

        # insert obrázku
        face = Image.open('./imgs/' + pics[cats.index(res[0][0])], 'r').convert('RGBA').resize((312, 600))

        top = 16
        for val in res:
            text = val[0].decode('utf-8') + ': ' + str(val[1]).replace('.', ',') + ' %'
            #offset = ((24 - len(text))/2) * 33
            draw.text((450, top), text, (0, 0, 0, 0), font=font)
            top += 88

        pattern.paste(face, box=(60, 15), mask=face)
        #zapsat obrazek
        out_img = io.BytesIO()
        pattern.save(out_img, format='PNG')

        putFile = s3.put_object(Bucket='datarozhlas', 
                                Key='profil-volice/share/' + name + '.png',
                                Body=out_img.getvalue(), 
                                ACL='public-read', 
                                ContentType='image/png')

        #zapsat html
        html = template.format(name, str(res[0][1]).replace('.', ',').replace(',0', ''), res[0][0])
        putFile = s3.put_object(Bucket='datarozhlas', 
                                Key='profil-volice/share/' + name + '.html', 
                                Body=html, 
                                ACL='public-read', 
                                ContentType='text/html')
        return name
