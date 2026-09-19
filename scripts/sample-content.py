import json, hashlib
from pathlib import Path
root=Path(__file__).resolve().parent.parent

def question(id,prompt,explanation,**kind):
    return dict(id=id,revision=1,prompt=prompt,difficulty='easy',explanation=explanation,**kind)
java=[question('java-types','Which type stores a true/false value?','`boolean` has exactly two values: `true` and `false`.',type='choice',options=['int','boolean','String','double'],correct=[1],multiple=False),
question('java-modifiers','Select both access modifiers.','`public` and `private` control access. `static` controls ownership; `final` prevents reassignment or extension.',type='choice',options=['public','static','private','final'],correct=[0,2],multiple=True),
question('java-blank','Complete the declaration: ___ count = 3;','`int` stores a 32-bit signed integer.',type='blanks',blanks=[dict(label='Type',accepted=['int'],case_sensitive=True)]),
question('java-sum','Write a complete `Main` program that reads two integers and prints their sum.','Read both values, add them, then print the sum.',type='java',style='program',starter='public class Main {\n    public static void main(String[] args) {\n        // Read two integers and print their sum.\n    }\n}',template='',reference='public class Main { public static void main(String[] args) { java.util.Scanner s = new java.util.Scanner(System.in); System.out.println(s.nextInt() + s.nextInt()); } }',cases=[dict(name='Positive numbers',stdin='2 3\n',expected='5\n'),dict(name='Negative number',stdin='-4 7\n',expected='3\n')]),
question('java-method','Complete `square(int n)` by writing its method body.','Multiplying an integer by itself gives its square.',type='java',style='snippet',starter='return n;',template='public class Main {\n    public static int square(int n) {\n        {{answer}}\n    }\n}',reference='return n * n;',cases=[dict(name='Positive',stdin='',expected='25',harness='System.out.print(Main.square(5));'),dict(name='Negative',stdin='',expected='9',harness='System.out.print(Main.square(-3));')])]
math=[question('math-square','What is 7 × 8?','Seven groups of eight make 56.',type='choice',options=['48','54','56','64'],correct=[2],multiple=False),question('math-equation','Solve 3x + 2 = 14.','Subtract 2, then divide by 3: x = 4.',type='blanks',blanks=[dict(label='x',accepted=['4','4.0'],case_sensitive=False)])]
science=[question('science-cell','Which structure contains most of a human cell’s genetic material?','The nucleus holds most DNA in human cells. Mitochondria also contain a small amount.',type='choice',options=['Cell membrane','Nucleus','Ribosome','Cytoplasm'],correct=[1],multiple=False),question('science-water','What is the chemical formula for water?','Water contains two hydrogen atoms and one oxygen atom.',type='blanks',blanks=[dict(label='Formula',accepted=['H2O','H₂O'],case_sensitive=True)])]
courses=[]
for slug,title,subject,description,notes,questions in [
('java','Java foundations','Programming / Java','Build confidence with types, methods, and small programs.','# Think in small steps\n\nJava programs group behavior into classes and methods. Start with types, then expressions, then control flow.\n\n```java\nint count = 3;\nboolean ready = true;\nSystem.out.println(count + 2);\n```\n\nA method can take inputs and return a result. Practice one concept at a time. The offline runner supports a subset of Java libraries.',java),
('math','Everyday algebra','Math','Strengthen arithmetic and solve simple equations.','# Keep both sides balanced\n\nApply the same operation to both sides of an equation.\n\nFor `3x + 2 = 14`, subtract 2 and divide by 3.',math),
('science','Cells and molecules','Science','Review a few building blocks of biology and chemistry.','# From molecules to cells\n\nWater is **H₂O**: two hydrogen atoms and one oxygen atom.\n\nHuman cells have specialized structures. The nucleus stores most genetic information.',science)]:
    courses.append(dict(schema_version=1,id=slug,title=title,description=description,subject=subject,difficulty='easy',lessons=[dict(id=slug+'-lesson',title='Start here',markdown=notes,test_ids=[slug+'-test'])],tests=[dict(id=slug+'-test',title=title+' practice',description='A short original practice set with immediate explanations.',difficulty='easy',questions=questions)]))
(root/'content/samples.json').write_text(json.dumps(courses,indent=2)+'\n')
entries=[]
for c in courses:
    data=(json.dumps(c,indent=2)+'\n').encode(); path=c['id']+'.json'; (root/'content'/path).write_bytes(data)
    entries.append({**{k:c[k] for k in ['id','title','description','subject','difficulty']},'path':path,'sha256':hashlib.sha256(data).hexdigest()})
(root/'content/catalog.json').write_text(json.dumps(dict(schema_version=1,collection_id='tutorialz-samples',courses=entries),indent=2)+'\n')
