// Distribution-equivalent parameter proposals for unchanged task_985ae207.generate.
// Different RNG stream; same uniform proposal laws and literal acceptance checks.
#include <algorithm>
#include <iostream>
#include <random>
#include <vector>
#include <array>
#include <fstream>
using namespace std;
int main(int argc,char**argv){
 ofstream parity;if(argc>3)parity.open(argv[3]);int parity_count=0;
 int count=argc>1?stoi(argv[1]):1000;unsigned seed=argc>2?stoul(argv[2]):10910000;
 for(int episode=0;episode<count;++episode){
  mt19937 rng(seed+episode);auto ri=[&](int a,int b){return uniform_int_distribution<int>(a,b)(rng);};
  int size=ri(0,3)?20:25,boxes=size==25?4:ri(2,3),pixels=boxes+ri(0,1);
  vector<int> colours;for(int c=1;c<=9;++c)if(c!=8)colours.push_back(c);
  int fi=ri(0,(int)colours.size()-1),frame=colours[fi];colours.erase(colours.begin()+fi);shuffle(colours.begin(),colours.end(),rng);colours.resize(boxes);
  vector<int> pc(pixels);for(;;){vector<bool>seen(boxes);for(int&i:pc){i=ri(0,boxes-1);seen[i]=true;}if(all_of(seen.begin(),seen.end(),[](bool x){return x;}))break;}
  vector<int> wide(boxes),tall(boxes),br(boxes),bc(boxes),pr(pixels),pq(pixels);unsigned long long attempts=0;
  for(;;){++attempts;
   vector<int>shorts(boxes),longs(boxes),dirs(boxes);for(int&i:shorts)i=ri(2,4);for(int&i:longs)i=ri(5,18);for(int&i:dirs)i=ri(0,1);
   for(int i=0;i<boxes;++i){wide[i]=dirs[i]?shorts[i]:longs[i];tall[i]=dirs[i]?longs[i]:shorts[i];br[i]=ri(0,size-tall[i]);bc[i]=ri(0,size-wide[i]);}
   for(int&i:pr)i=ri(2,size-3);for(int&i:pq)i=ri(2,size-3);
   auto emit_check=[&](bool accepted){
    if(!parity.is_open()||parity_count>=2000)return;++parity_count;
    parity<<"{\"size\":"<<size<<",\"fcolor\":"<<frame;
    auto field=[&](const char*name,const vector<int>&a){parity<<",\""<<name<<"\":[";for(int i=0;i<(int)a.size();++i){if(i)parity<<",";parity<<a[i];}parity<<"]";};
    field("wides",wide);field("talls",tall);field("brows",br);field("bcols",bc);field("bcolors",colours);field("prows",pr);field("pcols",pq);vector<int>pcolours;for(int b:pc)pcolours.push_back(colours[b]);field("pcolors",pcolours);parity<<",\"_accepted\":"<<(accepted?"true":"false")<<"}"<<endl;
   };
   bool good=true;
   // Early necessary checks cannot discard a native-valid sample; all random parameters drawn.
   for(int i=0;i<pixels&&good;++i){int b=pc[i],r=pr[i],c=pq[i];bool inr=br[b]<=r&&r<br[b]+tall[b],inc=bc[b]<=c&&c<bc[b]+wide[b];if(inr==inc){good=false;break;}}
   if(!good){emit_check(false);continue;}
   vector<array<int,4>>rects;for(int i=0;i<boxes;++i)rects.push_back({br[i],bc[i],tall[i],wide[i]});for(int i=0;i<pixels;++i)rects.push_back({pr[i]-1,pq[i]-1,3,3});
   for(int i=0;i<(int)rects.size()&&good;++i)for(int j=0;j<i;++j){auto a=rects[i],b=rects[j];if(a[0]+a[2]+1<=b[0]||b[0]+b[2]+1<=a[0]||a[1]+a[3]+1<=b[1]||b[1]+b[3]+1<=a[1])continue;good=false;break;}
   if(!good){emit_check(false);continue;}
   int output[25][25];fill(&output[0][0],&output[0][0]+625,8);
   for(int i=0;i<boxes;++i)for(int r=br[i];r<br[i]+tall[i];++r)for(int c=bc[i];c<bc[i]+wide[i];++c)output[r][c]=colours[i];
   for(int i=0;i<pixels&&good;++i){int b=pc[i],r=pr[i],c=pq[i],last=-1;
    for(;;){
     for(int dr=-1;dr<=1&&good;++dr)for(int dc=-1;dc<=1;++dc){int y=r+dr,x=c+dc;if(y<0||y>=size||x<0||x>=size||(output[y][x]!=8&&output[y][x]!=colours[b])){good=false;break;}output[y][x]=frame;}
     if(!good)break;output[r][c]=colours[b];vector<int>ds;
     if(r<br[b])ds.push_back(1);if(r>=br[b]+tall[b])ds.push_back(2);if(c<bc[b])ds.push_back(3);if(c>=bc[b]+wide[b])ds.push_back(4);
     if(ds.empty())break;if(ds.size()>1||(last!=-1&&last!=ds[0])){good=false;break;}last=ds[0];if(last==1)r+=3;if(last==2)r-=3;if(last==3)c+=3;if(last==4)c-=3;
    }
   }
   emit_check(good);if(good)break;
  }
  cout<<"{\"size\":"<<size<<",\"fcolor\":"<<frame;
  auto field=[&](const char*name,const vector<int>&a){cout<<",\""<<name<<"\":[";for(int i=0;i<(int)a.size();++i){if(i)cout<<",";cout<<a[i];}cout<<"]";};
  field("wides",wide);field("talls",tall);field("brows",br);field("bcols",bc);field("bcolors",colours);field("prows",pr);field("pcols",pq);vector<int>pcolours;for(int b:pc)pcolours.push_back(colours[b]);field("pcolors",pcolours);cout<<",\"_attempts\":"<<attempts<<",\"_seed\":"<<seed+episode<<"}"<<endl;
 }
}
