from __future__ import print_function, division

import numpy as np
import openmdao.api as om


class ComputeLift(om.ExplicitComponent):
    
    def initialize(self):
        self.options.declare('num_nodes', types=int, default=1)

    def setup(self):
        nn = self.options['num_nodes']

        self.add_input('CL', val=0.5, shape=nn, desc='coefficient of lift', units=None)
        self.add_input('rho', val=1.2, shape=nn, desc='air density', units='kg/m**3')
        self.add_input('velocity', val=100., shape=nn, desc='aircraft velocity', units='m/s')
        self.add_input('S_ref', val=8., shape=nn, desc='wing reference area', units='m**2')

        self.add_output('lift', val=np.zeros(nn), desc='aircraft lift', units='N')
        
        # Sparse partials
        arange = np.arange(nn)
        self.declare_partials('*', '*', rows=arange, cols=arange)
        
    def compute(self, inputs, outputs):
        CL = inputs['CL']
        rho = inputs['rho']
        velocity = inputs['velocity']
        S_ref = inputs['S_ref']
        
        outputs['lift'] = 0.5 * CL * rho * velocity**2 * S_ref
        
    def compute_partials(self, inputs, partials):
        nn = self.options['num_nodes']
        
        CL = inputs['CL']
        rho = inputs['rho']
        velocity = inputs['velocity']
        S_ref = inputs['S_ref']

        # Sparse partials
        partials['lift', 'CL'] = rho * velocity**2 * S_ref
        partials['lift', 'rho'] = 0.5 * CL * velocity**2 * S_ref
        partials['lift', 'velocity'] = CL * rho * velocity * S_ref
        partials['lift', 'S_ref'] = 0.5 * CL * rho * velocity**2       


if __name__ == "__main__":
    
    prob = om.Problem(model=om.Group())
    
    nn = 11
    
    ivc = prob.model.add_subsystem('indep_var_comp', om.IndepVarComp(), promotes=['*'])
    ivc.add_output('CL', val=0.5, shape=nn, units=None)
    ivc.add_output('rho', val=0.4, shape=nn, units='kg/m**3')
    ivc.add_output('velocity', val=np.linspace(100., 200., nn), units='m/s')
    ivc.add_output('S_ref', val=8., shape=nn, units='m**2')
    
    prob.model.add_subsystem('compute_lift', ComputeLift(num_nodes=nn), promotes=['*'])
    
    prob.setup()
    prob.run_model()
    
    prob.compute_totals(['lift'], ['CL', 'rho', 'velocity', 'S_ref'])
    
    print('Computed lift: {} Newtons'.format(prob['lift'][0]))

    check_partials_data = prob.check_partials(compact_print=True)

    om.partial_deriv_plot('lift', 'CL', check_partials_data)
